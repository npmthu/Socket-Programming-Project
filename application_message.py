import struct
from enum import Enum
from typing import Dict, Any


class MessageType(Enum):
    REQUEST = 1
    RESPONSE = 2
    RETRY = 3


class ActionCode(Enum):
    LOGIN = 1
    UPLOAD = 2
    DOWNLOAD = 3
    LIST_FILES = 4
    UPLOAD_FOLDER = 5 
    HEART_BEAT = 6


class StatusCode(Enum):
    SUCCESS = 0
    ERROR = 1


class Message:
    HEADER_FORMAT = "!BBBI"  # Format for header (1+1+1+4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, msg_type, action_code, status_code, payload: bytes = b""):
        self.msg_type = msg_type
        self.action_code = action_code
        self.status_code = status_code
        self.payload = payload
        self.payload_length = len(payload)

    def to_bytes(self) -> bytes:
        """Serialize the message to bytes for transmission."""
        header = struct.pack(
            self.HEADER_FORMAT,
            self.msg_type,
            self.action_code,
            self.status_code,
            self.payload_length,
        )
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Deserialize a message from bytes."""
        if len(data) < cls.HEADER_SIZE:
            raise ValueError("Insufficient data for header.")
        
        # Extract header
        header_data = data[:cls.HEADER_SIZE]
        payload = data[cls.HEADER_SIZE:]

        # Unpack header
        msg_type, action_code, status_code, payload_length = struct.unpack(
            cls.HEADER_FORMAT, header_data
        )

        # Validate payload length
        if len(payload) != payload_length:
            raise ValueError("Payload length mismatch.")

        return cls(
            msg_type=msg_type,
            action_code=action_code,
            status_code=status_code,
            payload=payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "msg_type": self.msg_type,
            "action_code": self.action_code,
            "status_code": self.status_code,
            "payload_length": self.payload_length,
            "payload": self.payload.decode("utf-8", errors="replace"),
        }

    

    def __repr__(self):
        return (
            f"Message(msg_type={self.msg_type}, action_code={self.action_code}, "
            f"status_code={self.status_code}, payload_length={self.payload_length})"
        )