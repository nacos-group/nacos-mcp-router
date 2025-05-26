#-*- coding: utf-8 -*-
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .logger import NacosMcpRouteLogger


@dataclass
class InputProperty:
    type: str
    description: str

    @classmethod
    def from_dict(cls, data: dict) -> "InputProperty":
        if data is None or len(data) == 0:
            return InputProperty(type="", description="")
        return cls(
            type=data["type"],
            description=data["description"]
        )

@dataclass
class InputSchema:
    type: str
    properties: Dict[str, InputProperty]

    @classmethod
    def from_dict(cls, data: dict) -> "InputSchema":
        if data is None or len(data) == 0:
            return InputSchema(type="", properties={})
        return cls(
            type=data["type"],
            properties={k: InputProperty.from_dict(v) for k, v in data["properties"].items()}
        )

@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict

    @classmethod
    def from_dict(cls, data: dict) -> "Tool":
        return cls(
            name=data["name"],
            description=data["description"],
            input_schema=data["inputSchema"]
        )

@dataclass
class ToolMeta:
    invoke_context: Dict[str, Any]
    enabled: bool
    templates: Dict[str, str]

    @classmethod
    def from_dict(cls, data: dict) -> "ToolMeta":
        return cls(
            invoke_context=data.get("invokeContext", {}),
            enabled=data.get("enabled", True),
            templates=data.get("templates", {})
        )

@dataclass
class ToolSpec:
    tools: List[Tool]
    tools_meta: Dict[str, ToolMeta]

    @classmethod
    def from_dict(cls, data: dict) -> "ToolSpec":
        return cls(
            tools=[Tool.from_dict(t) for t in data.get("tools", [])],
            tools_meta={k: ToolMeta.from_dict(v) for k, v in data.get("toolsMeta", {}).items()}
        )

# ------------------ 主结构 ------------------
@dataclass
class ServiceRef:
    namespace_id: str
    group_name: str
    service_name: str

    @classmethod
    def from_dict(cls, data: dict) -> "ServiceRef":
        if data is None or len(data) == 0:
            return ServiceRef(namespace_id="", group_name="", service_name="")
        return cls(
            namespace_id=data["namespaceId"],
            group_name=data["groupName"],
            service_name=data["serviceName"]
        )

@dataclass
class RemoteServerConfig:
    service_ref: ServiceRef
    export_path: str
    credentials: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "RemoteServerConfig":
        if data is None or len(data) == 0:
            return RemoteServerConfig(service_ref=ServiceRef.from_dict({}), export_path="", credentials={})
        return cls(
            service_ref=ServiceRef.from_dict(data["serviceRef"]),
            export_path=data["exportPath"],
            credentials=data.get("credentials", {})
        )

@dataclass
class BackendEndpoint:
    address: str
    port: int

    @classmethod
    def from_dict(cls, data: dict) -> "BackendEndpoint":
        if data is None or len(data) == 0:
            return BackendEndpoint(address="", port=-1)
        return cls(
            address=data["address"],
            port=data["port"]
        )

@dataclass
class NacosMcpServerConfig:
    name: str
    protocol: str
    description: str | None
    version: str
    id: str | None
    remote_server_config: RemoteServerConfig
    local_server_config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    capabilities: List[str] = field(default_factory=list)
    backend_endpoints: List[BackendEndpoint] = field(default_factory=list)
    tool_spec: ToolSpec = field(default_factory=lambda: ToolSpec(tools=[], tools_meta={}))

    @classmethod
    def from_dict(cls, data: dict) -> "NacosMcpServerConfig":
        tool_spec_data = data.get("toolSpec")
        backend_endpoints_data = data.get("backendEndpoints")
        try:
            return cls(
                name=data["name"],
                protocol=data["protocol"],
                description=data["description"],
                version=data["version"],
                remote_server_config=RemoteServerConfig.from_dict(data["remoteServerConfig"]),
                local_server_config=data.get("localServerConfig", {}) if data.get("localServerConfig") else {},
                enabled=data.get("enabled", True),
                capabilities=data.get("capabilities", []),
                backend_endpoints=[BackendEndpoint.from_dict(e) for e in data.get("backendEndpoints", [])] if backend_endpoints_data else [],
                tool_spec=ToolSpec.from_dict(tool_spec_data) if tool_spec_data else ToolSpec(tools=[], tools_meta={}),
                id=data["id"] if data.get("id") else None
            )
        except Exception as e:
            NacosMcpRouteLogger.get_logger().warning("failed to parse NacosMcpServerConfig from data: %s", data,  exc_info=e)
            raise Exception("failed to parse NacosMcpServerConfig from data")

    @classmethod
    def from_string(cls, string: str) -> "NacosMcpServerConfig":
        return cls.from_dict(json.loads(string))

    def get_tool_description(self) -> str:
        des = "" if self.description is None else self.description
        for tool in self.tool_spec.tools:
            if tool.description is not None:
                des += "\n" + tool.description

        return des
