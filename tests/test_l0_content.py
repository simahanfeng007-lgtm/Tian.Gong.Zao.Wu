from dataclasses import FrozenInstanceError

from tiangong_kernel.l0_primitives import stable_hash, stable_json_dumps, to_primitive
from tiangong_kernel.l0_primitives.content import (
    ContentDigest,
    ContentDispositionRef,
    ContentEncoding,
    ContentKind,
    ContentLength,
    ContentRef,
    ContentSafetyRef,
    MediaTypeKind,
    MediaTypeRef,
    PayloadDigest,
    PayloadKind,
    PayloadRef,
)
from tiangong_kernel.l0_primitives.identity import RefId


def test_content_construction_immutability_serialization_and_hash():
    content_ref = ContentRef(RefId("content:" + "2" * 32))
    payload_ref = PayloadRef(RefId("payload:" + "3" * 32), kind=PayloadKind.DIGEST_ONLY)
    facts = (
        content_ref,
        ContentDigest("sha256", "a" * 64),
        ContentEncoding("utf-8"),
        ContentLength(128),
        payload_ref,
        PayloadDigest("sha256", "b" * 64),
        MediaTypeRef("text/plain", kind=MediaTypeKind.TEXT),
        ContentDispositionRef("reference", filename_hint="note.txt"),
        ContentSafetyRef("unknown"),
    )
    assert to_primitive(payload_ref)["kind"] == "digest_only"
    assert stable_json_dumps(facts) == stable_json_dumps(facts)
    assert stable_hash(facts) == stable_hash(facts)
    try:
        content_ref.schema_version = "0.2"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("ContentRef allowed mutation")


def test_content_enum_values_are_stable():
    assert [item.value for item in ContentKind] == ["text", "json", "markdown", "image", "audio", "video", "binary", "structured", "unknown"]
    assert [item.value for item in PayloadKind] == ["inline_ref", "external_ref", "digest_only", "redacted", "unknown"]
    assert MediaTypeKind.APPLICATION.value == "application"
