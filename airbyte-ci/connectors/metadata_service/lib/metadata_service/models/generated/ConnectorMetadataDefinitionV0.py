# generated by datamodel-codegen:
#   filename:  ConnectorMetadataDefinitionV0.yaml

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import AnyUrl, BaseModel, Extra, Field, constr
from typing_extensions import Literal


class ConnectorBuildOptions(BaseModel):
    class Config:
        extra = Extra.forbid

    baseImage: Optional[str] = None


class ReleaseStage(BaseModel):
    __root__: Literal["alpha", "beta", "generally_available", "custom"] = Field(
        ...,
        description="enum that describes a connector's release stage",
        title="ReleaseStage",
    )


class SupportLevel(BaseModel):
    __root__: Literal["community", "certified"] = Field(
        ...,
        description="enum that describes a connector's release stage",
        title="SupportLevel",
    )


class AllowedHosts(BaseModel):
    class Config:
        extra = Extra.allow

    hosts: Optional[List[str]] = Field(
        None,
        description="An array of hosts that this connector can connect to.  AllowedHosts not being present for the source or destination means that access to all hosts is allowed.  An empty list here means that no network access is granted.",
    )


class NormalizationDestinationDefinitionConfig(BaseModel):
    class Config:
        extra = Extra.allow

    normalizationRepository: str = Field(
        ...,
        description="a field indicating the name of the repository to be used for normalization. If the value of the flag is NULL - normalization is not used.",
    )
    normalizationTag: str = Field(
        ...,
        description="a field indicating the tag of the docker repository to be used for normalization.",
    )
    normalizationIntegrationType: str = Field(
        ...,
        description="a field indicating the type of integration dialect to use for normalization.",
    )


class SuggestedStreams(BaseModel):
    class Config:
        extra = Extra.allow

    streams: Optional[List[str]] = Field(
        None,
        description="An array of streams that this connector suggests the average user will want.  SuggestedStreams not being present for the source means that all streams are suggested.  An empty list here means that no streams are suggested.",
    )


class ResourceRequirements(BaseModel):
    class Config:
        extra = Extra.forbid

    cpu_request: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_request: Optional[str] = None
    memory_limit: Optional[str] = None


class JobType(BaseModel):
    __root__: Literal[
        "get_spec",
        "check_connection",
        "discover_schema",
        "sync",
        "reset_connection",
        "connection_updater",
        "replicate",
    ] = Field(
        ...,
        description="enum that describes the different types of jobs that the platform runs.",
        title="JobType",
    )


class StreamBreakingChangeScope(BaseModel):
    class Config:
        extra = Extra.forbid

    affected_streams: List[str] = Field(
        ...,
        description="List of streams that are affected by the breaking change.",
        min_items=1,
    )


class AffectedStreamField(BaseModel):
    class Config:
        extra = Extra.forbid

    stream: str = Field(
        ..., description="The stream that is affected by the breaking change."
    )
    field: str = Field(
        ..., description="The field that is affected by the breaking change."
    )


class StreamFieldBreakingChangeScope(BaseModel):
    class Config:
        extra = Extra.forbid

    affected_stream_fields: List[AffectedStreamField] = Field(
        ...,
        description="List of streams that are affected by the breaking change.",
        min_items=1,
    )


class FieldBreakingChangeScope(BaseModel):
    __root__: Any


class AirbyteInternal(BaseModel):
    class Config:
        extra = Extra.allow

    sl: Optional[Literal[100, 200, 300]] = None
    ql: Optional[Literal[100, 200, 300, 400, 500, 600]] = None


class JobTypeResourceLimit(BaseModel):
    class Config:
        extra = Extra.forbid

    jobType: JobType
    resourceRequirements: ResourceRequirements


class BreakingChangeScope(BaseModel):
    __root__: Union[StreamBreakingChangeScope, FieldBreakingChangeScope] = Field(
        ...,
        description="A scope that can be used to limit the impact of a breaking change.",
    )


class ActorDefinitionResourceRequirements(BaseModel):
    class Config:
        extra = Extra.forbid

    default: Optional[ResourceRequirements] = Field(
        None,
        description="if set, these are the requirements that should be set for ALL jobs run for this actor definition.",
    )
    jobSpecific: Optional[List[JobTypeResourceLimit]] = None


class VersionBreakingChange(BaseModel):
    class Config:
        extra = Extra.forbid

    upgradeDeadline: date = Field(
        ...,
        description="The deadline by which to upgrade before the breaking change takes effect.",
    )
    message: str = Field(
        ..., description="Descriptive message detailing the breaking change."
    )
    migrationDocumentationUrl: Optional[AnyUrl] = Field(
        None,
        description="URL to documentation on how to migrate to the current version. Defaults to ${documentationUrl}-migrations#${version}",
    )
    impactLimitedToScopes: Optional[List[BreakingChangeScope]] = Field(
        None,
        description="List of scopes that are affected by the breaking change. If not specified, the breaking change cannot be scoped to smaller impact via the supported scope types.",
        min_items=1,
    )


class RegistryOverrides(BaseModel):
    class Config:
        extra = Extra.forbid

    enabled: bool
    name: Optional[str] = None
    dockerRepository: Optional[str] = None
    dockerImageTag: Optional[str] = None
    supportsDbt: Optional[bool] = None
    supportsNormalization: Optional[bool] = None
    license: Optional[str] = None
    documentationUrl: Optional[AnyUrl] = None
    connectorSubtype: Optional[str] = None
    allowedHosts: Optional[AllowedHosts] = None
    normalizationConfig: Optional[NormalizationDestinationDefinitionConfig] = None
    suggestedStreams: Optional[SuggestedStreams] = None
    resourceRequirements: Optional[ActorDefinitionResourceRequirements] = None


class ConnectorBreakingChanges(BaseModel):
    class Config:
        extra = Extra.forbid

    __root__: Dict[constr(regex=r"^\d+\.\d+\.\d+$"), VersionBreakingChange] = Field(
        ...,
        description="Each entry denotes a breaking change in a specific version of a connector that requires user action to upgrade.",
    )


class Registry(BaseModel):
    class Config:
        extra = Extra.forbid

    oss: Optional[RegistryOverrides] = None
    cloud: Optional[RegistryOverrides] = None


class ConnectorReleases(BaseModel):
    class Config:
        extra = Extra.forbid

    breakingChanges: ConnectorBreakingChanges
    migrationDocumentationUrl: Optional[AnyUrl] = Field(
        None,
        description="URL to documentation on how to migrate from the previous version to the current version. Defaults to ${documentationUrl}-migrations",
    )


class Data(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str
    icon: Optional[str] = None
    definitionId: UUID
    connectorBuildOptions: Optional[ConnectorBuildOptions] = None
    connectorType: Literal["destination", "source"]
    dockerRepository: str
    dockerImageTag: str
    supportsDbt: Optional[bool] = None
    supportsNormalization: Optional[bool] = None
    license: str
    documentationUrl: AnyUrl
    githubIssueLabel: str
    maxSecondsBetweenMessages: Optional[int] = Field(
        None,
        description="Maximum delay between 2 airbyte protocol messages, in second. The source will timeout if this delay is reached",
    )
    releaseDate: Optional[date] = Field(
        None,
        description="The date when this connector was first released, in yyyy-mm-dd format.",
    )
    protocolVersion: Optional[str] = Field(
        None, description="the Airbyte Protocol version supported by the connector"
    )
    connectorSubtype: Literal[
        "api",
        "database",
        "datalake",
        "file",
        "custom",
        "message_queue",
        "unknown",
        "vectorstore",
    ]
    releaseStage: ReleaseStage
    supportLevel: Optional[SupportLevel] = None
    tags: Optional[List[str]] = Field(
        [],
        description="An array of tags that describe the connector. E.g: language:python, keyword:rds, etc.",
    )
    registries: Optional[Registry] = None
    allowedHosts: Optional[AllowedHosts] = None
    releases: Optional[ConnectorReleases] = None
    normalizationConfig: Optional[NormalizationDestinationDefinitionConfig] = None
    suggestedStreams: Optional[SuggestedStreams] = None
    resourceRequirements: Optional[ActorDefinitionResourceRequirements] = None
    ab_internal: Optional[AirbyteInternal] = None


class ConnectorMetadataDefinitionV0(BaseModel):
    class Config:
        extra = Extra.forbid

    metadataSpecVersion: str
    data: Data
