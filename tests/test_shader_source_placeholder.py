import importlib
import sys
import types
import unittest
from types import SimpleNamespace


class _FakeShaderCompileFlag:
    def __init__(self):
        self.name = ""
        self.value = ""


class _FakeShaderCompileFlags:
    def __init__(self):
        self.flags = []


def _install_fake_renderdoc():
    sys.modules.setdefault(
        "renderdoc",
        types.SimpleNamespace(
            ShaderStage=SimpleNamespace(
                Vertex="vs",
                Hull="hs",
                Domain="ds",
                Geometry="gs",
                Pixel="ps",
                Compute="cs",
            ),
            ShaderCompileFlag=_FakeShaderCompileFlag,
            ShaderCompileFlags=_FakeShaderCompileFlags,
            ShaderEncoding=SimpleNamespace(HLSL=5, DXBC=1, DXIL=6, GLSL=2, SPIRV=3, Slang=9),
        ),
    )


_install_fake_renderdoc()

shader_module = importlib.import_module("bridge_extension.renderdoc_mcp_bridge.domains.shader")
base_module = importlib.import_module("bridge_extension.renderdoc_mcp_bridge.domains.base")

ShaderServiceMixin = shader_module.ShaderServiceMixin
BridgeService = base_module.BridgeService


class _FakePipe:
    def __init__(self, reflection):
        self._reflection = reflection

    def GetShader(self, _stage):
        return "ResourceId::1"

    def GetShaderEntryPoint(self, _stage):
        return "main"

    def GetShaderReflection(self, _stage):
        return self._reflection


class _FakeController:
    def __init__(self, reflection):
        self._pipe = _FakePipe(reflection)

    def SetFrameEvent(self, _eid, _force):
        return None

    def GetPipelineState(self):
        return self._pipe


class _FakeReplay:
    def __init__(self, reflection):
        self._controller = _FakeController(reflection)

    def BlockInvoke(self, fn):
        fn(self._controller)


class _FakeCtx:
    def __init__(self, reflection):
        self._reflection = reflection

    def IsCaptureLoaded(self):
        return True

    def Replay(self):
        return _FakeReplay(self._reflection)

    def GetResourceNameUnsuffixed(self, _rid):
        return ""

    def GetResourceName(self, _rid):
        return ""


class _TestShaderService(ShaderServiceMixin, BridgeService):
    def _shader_disasm(self, controller, pipe, stage_enum, reflection):
        return {
            "target": "DXBC",
            "text": "ps_5_0\nret",
            "line_count": 2,
            "error": None,
        }


class ShaderSourcePlaceholderTests(unittest.TestCase):
    def test_get_shader_source_rejects_false_placeholder(self):
        reflection = SimpleNamespace(
            debugInfo=SimpleNamespace(
                files=[SimpleNamespace(filename=-1, contents=False)],
                sourceDebugInformation=False,
                editBaseFile=-1,
                debuggable=True,
                debugStatus="",
                compiler="KnownShaderTool.fxc",
                encoding="Unknown",
            ),
            entryPoint="main",
        )
        service = _TestShaderService(_FakeCtx(reflection))

        result = service.get_shader_source({"eid": 14487, "stage": "ps"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["err"]["code"], "shader_source_unavailable")

    def test_get_shader_code_falls_back_to_disasm_for_false_placeholder(self):
        reflection = SimpleNamespace(
            debugInfo=SimpleNamespace(
                files=[SimpleNamespace(filename=-1, contents=False)],
                sourceDebugInformation=False,
                editBaseFile=-1,
                debuggable=True,
                debugStatus="",
                compiler="KnownShaderTool.fxc",
                encoding="Unknown",
            ),
            entryPoint="main",
        )
        service = _TestShaderService(_FakeCtx(reflection))

        result = service.get_shader_code({"eid": 14487, "stage": "ps"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["kind"], "disasm")
        self.assertEqual(result["data"]["debug"]["has_source"], False)
        self.assertEqual(result["data"]["code"]["text"], "ps_5_0\nret")

    def test_source_debug_information_still_works_when_file_entry_is_invalid(self):
        reflection = SimpleNamespace(
            debugInfo=SimpleNamespace(
                files=[SimpleNamespace(filename=-1, contents=False)],
                sourceDebugInformation="float4 main() : SV_Target { return 0; }\n",
                editBaseFile="DeferredLighting.ps.hlsl",
                debuggable=True,
                debugStatus="",
                compiler="KnownShaderTool.fxc",
                encoding="HLSL",
            ),
            entryPoint="main",
        )
        service = _TestShaderService(_FakeCtx(reflection))

        result = service.get_shader_code({"eid": 14487, "stage": "ps"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["kind"], "source")
        self.assertEqual(result["data"]["file"]["filename"], "DeferredLighting.ps.hlsl")
        self.assertIn("float4 main()", result["data"]["code"]["text"])
