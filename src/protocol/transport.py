"""
Unix domain socket transport for agent communication.

Provides async server and client for low-latency local communication on macOS.
"""

import asyncio
import json
import logging
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from src.protocol.message import AgentMessage, AgentType, MessageAck

logger = logging.getLogger(__name__)


@dataclass
class SocketConfig:
    """Configuration for Unix domain socket transport."""
    socket_dir: str = "/var/run/autonomous-glm"
    socket_timeout: float = 30.0
    buffer_size: int = 65536  # 64KB buffer
    max_message_size: int = 10 * 1024 * 1024  # 10MB max message
    
    def get_socket_path(self, agent: AgentType) -> str:
        """Get the socket path for a specific agent."""
        return os.path.join(self.socket_dir, f"{agent.value}.sock")


class TransportError(Exception):
    """Raised when transport operations fail."""
    pass


class ConnectionError(TransportError):
    """Raised when connection cannot be established."""
    pass


class MessageFramingError(TransportError):
    """Raised when message framing fails."""
    pass


class UnixSocketServer:
    """
    Async Unix domain socket server.
    
    Listens for incoming messages from other agents.
    """
    
    def __init__(
        self,
        socket_path: str,
        config: Optional[SocketConfig] = None,
        message_handler: Optional[Callable[[AgentMessage], MessageAck]] = None,
    ):
        """
        Initialize the socket server.
        
        Args:
            socket_path: Path to the socket file
            config: Socket configuration
            message_handler: Optional handler for received messages
        """
        self.socket_path = socket_path
        self.config = config or SocketConfig()
        self.message_handler = message_handler
        self._server: Optional[asyncio.Server] = None
        self._running = False
    
    async def start(self) -> None:
        """
        Start the socket server.
        
        Creates the socket directory if needed and begins listening.
        
        Raises:
            TransportError: If server cannot be started
        """
        # Ensure socket directory exists
        socket_dir = os.path.dirname(self.socket_path)
        if socket_dir:
            os.makedirs(socket_dir, mode=0o755, exist_ok=True)
        
        # Remove stale socket file if it exists
        if os.path.exists(self.socket_path):
            logger.warning(f"Removing stale socket file: {self.socket_path}")
            os.unlink(self.socket_path)
        
        try:
            self._server = await asyncio.start_unix_server(
                self._handle_connection,
                path=self.socket_path,
            )
            self._running = True
            logger.info(f"Socket server started at {self.socket_path}")
        except OSError as e:
            raise TransportError(f"Failed to start socket server: {e}")
    
    async def stop(self) -> None:
        """Stop the socket server and clean up."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        
        # Clean up socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
            logger.info(f"Removed socket file: {self.socket_path}")
    
    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Handle an incoming connection.
        
        Args:
            reader: Stream reader for incoming data
            writer: Stream writer for outgoing data
        """
        peer = writer.get_extra_info('peername') or 'unknown'
        logger.debug(f"New connection from {peer}")
        
        try:
            while self._running:
                # Read message with timeout
                try:
                    message_data = await asyncio.wait_for(
                        self._read_message(reader),
                        timeout=self.config.socket_timeout,
                    )
                except asyncio.TimeoutError:
                    logger.debug(f"Connection timeout from {peer}")
                    break
                
                if not message_data:
                    logger.debug(f"Connection closed by {peer}")
                    break
                
                # Parse and handle message
                try:
                    message = AgentMessage.from_json(message_data)
                    logger.debug(f"Received message {message.message_id}")
                    
                    # Call handler if set
                    if self.message_handler:
                        ack = self.message_handler(message)
                        ack_data = ack.to_json().encode('utf-8')
                        await self._write_message(writer, ack_data)
                    else:
                        # Send default ack
                        ack = MessageAck(
                            message_id=message.message_id,
                            status="acknowledged",
                        )
                        ack_data = ack.to_json().encode('utf-8')
                        await self._write_message(writer, ack_data)
                        
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    # Send error ack
                    ack = MessageAck(
                        message_id="error",
                        status="error",
                        error_message=str(e),
                    )
                    ack_data = ack.to_json().encode('utf-8')
                    await self._write_message(writer, ack_data)
                    
        except Exception as e:
            logger.error(f"Connection error from {peer}: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
    
    async def _read_message(self, reader: asyncio.StreamReader) -> Optional[bytes]:
        """
        Read a length-prefixed message from the stream.
        
        Uses 4-byte length prefix for framing.
        
        Args:
            reader: Stream reader
            
        Returns:
            Message bytes or None if connection closed
            
        Raises:
            MessageFramingError: If message framing is invalid
        """
        # Read length prefix (4 bytes, big-endian)
        length_data = await reader.readexactly(4)
        if not length_data:
            return None
        
        length = struct.unpack('>I', length_data)[0]
        
        if length > self.config.max_message_size:
            raise MessageFramingError(
                f"Message size {length} exceeds maximum {self.config.max_message_size}"
            )
        
        if length == 0:
            return None
        
        # Read message data
        message_data = await reader.readexactly(length)
        return message_data
    
    async def _write_message(
        self,
        writer: asyncio.StreamWriter,
        data: bytes,
    ) -> None:
        """
        Write a length-prefixed message to the stream.
        
        Args:
            writer: Stream writer
            data: Message bytes to write
        """
        # Write length prefix (4 bytes, big-endian)
        length = len(data)
        length_data = struct.pack('>I', length)
        writer.write(length_data)
        writer.write(data)
        await writer.drain()


class UnixSocketClient:
    """
    Async Unix domain socket client.
    
    Connects to other agents' socket servers.
    """
    
    def __init__(self, config: Optional[SocketConfig] = None):
        """
        Initialize the socket client.
        
        Args:
            config: Socket configuration
        """
        self.config = config or SocketConfig()
        self._connections: dict[str, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
    
    async def connect(self, agent: AgentType) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """
        Connect to an agent's socket server.
        
        Args:
            agent: Target agent to connect to
            
        Returns:
            Tuple of (reader, writer) for the connection
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        socket_path = self.config.get_socket_path(agent)
        
        # Check for cached connection
        if socket_path in self._connections:
            reader, writer = self._connections[socket_path]
            # Check if connection is still valid
            if not writer.is_closing():
                return reader, writer
            else:
                del self._connections[socket_path]
        
        # Establish new connection
        if not os.path.exists(socket_path):
            raise ConnectionError(f"Socket not found: {socket_path}")
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=self.config.socket_timeout,
            )
            self._connections[socket_path] = (reader, writer)
            logger.debug(f"Connected to {socket_path}")
            return reader, writer
        except asyncio.TimeoutError:
            raise ConnectionError(f"Connection timeout to {socket_path}")
        except OSError as e:
            raise ConnectionError(f"Failed to connect to {socket_path}: {e}")
    
    async def disconnect(self, agent: AgentType) -> None:
        """
        Disconnect from an agent's socket server.
        
        Args:
            agent: Agent to disconnect from
        """
        socket_path = self.config.get_socket_path(agent)
        if socket_path in self._connections:
            _, writer = self._connections[socket_path]
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            del self._connections[socket_path]
            logger.debug(f"Disconnected from {socket_path}")
    
    async def disconnect_all(self) -> None:
        """Disconnect from all agents."""
        for agent in list(AgentType):
            try:
                await self.disconnect(agent)
            except Exception:
                pass
    
    async def send_message(
        self,
        agent: AgentType,
        message: AgentMessage,
        wait_for_ack: bool = True,
    ) -> Optional[MessageAck]:
        """
        Send a message to an agent.
        
        Args:
            agent: Target agent
            message: Message to send
            wait_for_ack: Whether to wait for acknowledgment
            
        Returns:
            MessageAck if wait_for_ack is True, else None
            
        Raises:
            ConnectionError: If connection cannot be established
            TransportError: If send fails
        """
        reader, writer = await self.connect(agent)
        
        try:
            # Serialize and send message
            message_data = message.to_json().encode('utf-8')
            await self._write_message(writer, message_data)
            logger.debug(f"Sent message {message.message_id} to {agent.value}")
            
            if wait_for_ack:
                # Read acknowledgment
                ack_data = await asyncio.wait_for(
                    self._read_message(reader),
                    timeout=self.config.socket_timeout,
                )
                if ack_data:
                    ack = MessageAck.from_json(ack_data)
                    logger.debug(f"Received ack for {message.message_id}: {ack.status}")
                    return ack
                else:
                    raise TransportError("No acknowledgment received")
            
            return None
            
        except asyncio.TimeoutError:
            raise TransportError(f"Acknowledgment timeout from {agent.value}")
        except Exception as e:
            # Invalidate connection on error
            socket_path = self.config.get_socket_path(agent)
            if socket_path in self._connections:
                del self._connections[socket_path]
            raise TransportError(f"Failed to send message to {agent.value}: {e}")
    
    async def _read_message(self, reader: asyncio.StreamReader) -> Optional[bytes]:
        """Read a length-prefixed message from the stream."""
        # Read length prefix (4 bytes, big-endian)
        try:
            length_data = await reader.readexactly(4)
        except asyncio.IncompleteReadError:
            return None
        
        length = struct.unpack('>I', length_data)[0]
        
        if length > self.config.max_message_size:
            raise MessageFramingError(
                f"Message size {length} exceeds maximum {self.config.max_message_size}"
            )
        
        if length == 0:
            return None
        
        # Read message data
        message_data = await reader.readexactly(length)
        return message_data
    
    async def _write_message(
        self,
        writer: asyncio.StreamWriter,
        data: bytes,
    ) -> None:
        """Write a length-prefixed message to the stream."""
        # Write length prefix (4 bytes, big-endian)
        length = len(data)
        length_data = struct.pack('>I', length)
        writer.write(length_data)
        writer.write(data)
        await writer.drain()


async def send_message(
    agent: AgentType,
    message: AgentMessage,
    config: Optional[SocketConfig] = None,
    wait_for_ack: bool = True,
) -> Optional[MessageAck]:
    """
    Send a message to an agent using a temporary client.
    
    Convenience function for one-off message sends.
    
    Args:
        agent: Target agent
        message: Message to send
        config: Socket configuration
        wait_for_ack: Whether to wait for acknowledgment
        
    Returns:
        MessageAck if wait_for_ack is True, else None
    """
    client = UnixSocketClient(config)
    try:
        return await client.send_message(agent, message, wait_for_ack)
    finally:
        await client.disconnect_all()


async def broadcast(
    message: AgentMessage,
    agents: Optional[list[AgentType]] = None,
    config: Optional[SocketConfig] = None,
) -> list[tuple[AgentType, Optional[MessageAck], Optional[Exception]]]:
    """
    Broadcast a message to multiple agents.
    
    Args:
        message: Message to broadcast
        agents: List of target agents (defaults to all non-human agents)
        config: Socket configuration
        
    Returns:
        List of (agent, ack, error) tuples for each agent
    """
    if agents is None:
        agents = [AgentType.CLAUDE, AgentType.MINIMAX, AgentType.CODEX]
    
    client = UnixSocketClient(config)
    results: list[tuple[AgentType, Optional[MessageAck], Optional[Exception]]] = []
    
    try:
        for agent in agents:
            try:
                ack = await client.send_message(agent, message)
                results.append((agent, ack, None))
            except Exception as e:
                results.append((agent, None, e))
    finally:
        await client.disconnect_all()
    
    return results