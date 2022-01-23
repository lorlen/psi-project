from enum import Enum
from ipaddress import ip_address, IPv4Address, IPv6Address
from struct import Struct
from typing import Optional, Union


# Define action constants.
class ActionCode(Enum):
    ASK_IF_FILE_EXISTS = 10
    ANSWER_FILE_EXISTS = 20
    START_DOWNLOADING = 30
    CONFIRMATION = 40
    REVOKE = 50


# Define status constants.
class StatusCode(Enum):
    NOT_APPLICABLE = 1
    ACCEPT = 200
    FILE_EXISTS = 201
    FILE_NOT_FOUND = 404
    BAD_REQUEST = 400
    UPLOAD_CANCELED = 202


class IPAddrKind(Enum):
    NONE = 0
    IPv4 = 4
    IPv6 = 6


class Message:
    struct_def = Struct("!hhb16sl256s")

    def __init__(
        self,
        actionCode: ActionCode,
        status: StatusCode,
        owner_address: Optional[Union[str, IPv4Address, IPv6Address]],
        details: str = "",
    ):
        self.actionCode = actionCode
        self.status = status
        self.owner_address = owner_address
        self.address_kind = IPAddrKind.NONE
        self.detailsLength = len(details)
        self.details = details

        if isinstance(owner_address, str):
            self.owner_address = ip_address(owner_address)

        if isinstance(self.owner_address, IPv4Address):
            self.address_kind = IPAddrKind.IPv4
        elif isinstance(self.owner_address, IPv6Address):
            self.address_kind = IPAddrKind.IPv6

    def __str__(self) -> str:
        return "".join(
            [
                "actionCode: {}\n".format(self.actionCode.name),
                "status: {}\n".format(self.status.name),
                "owner_address: {}\n".format(self.owner_address),
                "detailsLength: {}\n".format(self.detailsLength),
                "details: {}\n".format(self.details),
            ]
        )

    def message_to_bytes(self):
        return self.struct_def.pack(
            self.actionCode.value,
            self.status.value,
            self.address_kind.value,
            self.owner_address.packed.ljust(16, b"\0")
            if self.owner_address
            else b"\0" * 16,
            self.detailsLength,
            self.details.encode("utf-8"),
        )

    @staticmethod
    def bytes_to_message(message):
        data = Message.struct_def.unpack(message)

        if IPAddrKind(data[2]) == IPAddrKind.IPv4:
            addr = IPv4Address(data[3][:4])
        elif IPAddrKind(data[2]) == IPAddrKind.IPv6:
            addr = IPv6Address(data[3])
        else:
            addr = None

        return Message(
            ActionCode(data[0]),
            StatusCode(data[1]),
            addr,
            data[5].decode("utf-8").rstrip("\x00"),
        )
