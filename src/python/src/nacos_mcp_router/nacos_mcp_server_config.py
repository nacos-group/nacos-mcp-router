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
    input_schema: InputSchema

    @classmethod
    def from_dict(cls, data: dict) -> "Tool":
        return cls(
            name=data["name"],
            description=data["description"],
            input_schema=InputSchema.from_dict(data["inputSchema"])
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
                tool_spec=ToolSpec.from_dict(tool_spec_data) if tool_spec_data else ToolSpec(tools=[], tools_meta={})
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

if __name__ == "__main__":
    json_str = '{"code":0,"message":"success","data":{"name":"amap-mcp-server","protocol":"stdio","description":"高德地图服务,提供经纬度和行政区划相互转换、IP地址定位、周边搜、路径规划、距离测量、天气等相关工具","version":"0.1.0","remoteServerConfig":null,"localServerConfig":{"mcpServers":{"amap-mcp-server":{"description":"高德地图服务","command":"npx","args":["-y","@amap/amap-maps-mcp-server"],"env":{"AMAP_MAPS_API_KEY":"524c718bd13fee1825fbdf20d8844105"}}}},"credentials":{},"enabled":true,"capabilities":["TOOL"],"backendEndpoints":null,"toolSpec":{"tools":[{"name":"maps_regeocode","description":"将一个高德经纬度坐标转换为行政区划地址信息","inputSchema":{"type":"object","properties":[{"label":"location","type":"string","description":"经纬度","children":[],"key":"args@@location"}]}},{"name":"maps_geo","description":"将详细的结构化地址转换为经纬度坐标。支持对地标性名胜景区、建筑物名称解析为经纬度坐标","inputSchema":{"type":"object","properties":{"address":{"type":"string","description":"待解析的结构化地址信息"},"city":{"type":"string","description":"指定查询的城市"}},"required":["address"]}},{"name":"maps_ip_location","description":"IP 定位根据用户输入的 IP 地址，定位 IP 的所在位置","inputSchema":{"type":"object","properties":{"ip":{"type":"string","description":"IP地址"}},"required":["ip"]}},{"name":"maps_weather","description":"根据城市名称或者标准adcode查询指定城市的天气","inputSchema":{"type":"object","properties":[{"label":"city","type":"string","description":"城市名称或者adcode","children":[],"key":"args@@city"}]}},{"name":"maps_search_detail","description":"查询关键词搜或者周边搜获取到的POI ID的详细信息","inputSchema":{"type":"object","properties":{"id":{"type":"string","description":"关键词搜或者周边搜获取到的POI ID"}},"required":["id"]}},{"name":"maps_bicycling","description":"骑行路径规划用于规划骑行通勤方案，规划时会考虑天桥、单行线、封路等情况。最大支持 500km 的骑行路线规划","inputSchema":{"type":"object","properties":{"origin":{"type":"string","description":"出发点经纬度，坐标格式为：经度，纬度"},"destination":{"type":"string","description":"目的地经纬度，坐标格式为：经度，纬度"}},"required":["origin","destination"]}},{"name":"maps_direction_walking","description":"步行路径规划 API 可以根据输入起点终点经纬度坐标规划100km 以内的步行通勤方案，并且返回通勤方案的数据","inputSchema":{"type":"object","properties":{"origin":{"type":"string","description":"出发点经度，纬度，坐标格式为：经度，纬度"},"destination":{"type":"string","description":"目的地经度，纬度，坐标格式为：经度，纬度"}},"required":["origin","destination"]}},{"name":"maps_direction_driving","description":"驾车路径规划 API 可以根据用户起终点经纬度坐标规划以小客车、轿车通勤出行的方案，并且返回通勤方案的数据。","inputSchema":{"type":"object","properties":{"origin":{"type":"string","description":"出发点经度，纬度，坐标格式为：经度，纬度"},"destination":{"type":"string","description":"目的地经度，纬度，坐标格式为：经度，纬度"}},"required":["origin","destination"]}},{"name":"maps_direction_transit_integrated","description":"公交路径规划 API 可以根据用户起终点经纬度坐标规划综合各类公共（火车、公交、地铁）交通方式的通勤方案，并且返回通勤方案的数据，跨城场景下必须传起点城市与终点城市","inputSchema":{"type":"object","properties":{"origin":{"type":"string","description":"出发点经度，纬度，坐标格式为：经度，纬度"},"destination":{"type":"string","description":"目的地经度，纬度，坐标格式为：经度，纬度"},"city":{"type":"string","description":"公共交通规划起点城市"},"cityd":{"type":"string","description":"公共交通规划终点城市"}},"required":["origin","destination","city","cityd"]}},{"name":"maps_distance","description":"距离测量 API 可以测量两个经纬度坐标之间的距离,支持驾车、步行以及球面距离测量","inputSchema":{"type":"object","properties":{"origins":{"type":"string","description":"起点经度，纬度，可以传多个坐标，使用分号隔离，比如120,30;120,31，坐标格式为：经度，纬度"},"destination":{"type":"string","description":"终点经度，纬度，坐标格式为：经度，纬度"},"type":{"type":"string","description":"距离测量类型,1代表驾车距离测量，0代表直线距离测量，3步行距离测量"}},"required":["origins","destination"]}},{"name":"maps_text_search","description":"关键词搜，根据用户传入关键词，搜索出相关的POI","inputSchema":{"type":"object","properties":{"keywords":{"type":"string","description":"搜索关键词"},"city":{"type":"string","description":"查询城市"},"types":{"type":"string","description":"POI类型，比如加油站"}},"required":["keywords"]}},{"name":"maps_around_search","description":"周边搜，根据用户传入关键词以及坐标location，搜索出radius半径范围的POI","inputSchema":{"type":"object","properties":{"keywords":{"type":"string","description":"搜索关键词"},"location":{"type":"string","description":"中心点经度纬度"},"radius":{"type":"string","description":"搜索半径"}},"required":["location"]}}],"toolsMeta":{"list_namespace":{"invokeContext":{"path":"/xxx","method":"GET"},"enabled":true,"templates":{"json-go-tamplate":{"templateType":"string","requestTemplate":{"url":"","method":"GET","headers":[],"argsToJsonBody":false,"argsToUrlParam":true,"argsToFormBody":true,"body":"string"},"responseTemplate":{"body":"string"}}}},"maps_geo":{"invokeContext":{},"enabled":true,"templates":{"":""}},"maps_regeocode":{"invokeContext":{"":""},"enabled":true,"templates":{}},"maps_weather":{"invokeContext":{"":""},"enabled":false,"templates":{}}}}}}'
    dct = json.loads(json_str)
    config = NacosMcpServerConfig.from_dict(dct['data'])
    print(config)