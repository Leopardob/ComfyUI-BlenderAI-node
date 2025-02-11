bl_info = {
    'name': '无限圣杯-节点',
    'author': '幻之境开发小组-会飞的键盘侠、只剩一瓶辣椒酱',
    'version': (1, 3, 7),
    'blender': (3, 0, 0),
    'location': '3DView->Panel',
    'category': '辣椒出品',
    'doc_url': "https://shimo.im/docs/Ee32m0w80rfLp4A2"
}
__dict__ = {}
import time
ts = time.time()
import bpy
import sys
from addon_utils import disable
from .SDNode import rtnode_unreg, TaskManager
from .MultiLineText import EnableMLT

from .translations import translations_dict
from .utils import Icon, FSWatcher, ScopeTimer
from .timer import timer_reg, timer_unreg
from .preference import pref_register, pref_unregister
from .ops import Ops, Ops_Mask, Load_History, Popup_Load, Copy_Tree, Load_Batch, Fetch_Node_Status, Sync_Stencil_Image, NodeSearch
from .ui import Panel, HISTORY_UL_UIList, HistoryItem
from .SDNode.history import History
from .SDNode.rt_tracker import reg_tracker, unreg_tracker
from .prop import RenderLayerString, Prop
from .Linker import linker_register, linker_unregister
from .hook import use_hook
clss = [Panel, Ops, RenderLayerString, Prop, HISTORY_UL_UIList, HistoryItem, Ops_Mask, Load_History, Popup_Load, Copy_Tree, Load_Batch, Fetch_Node_Status, Sync_Stencil_Image, NodeSearch, EnableMLT]
reg, unreg = bpy.utils.register_classes_factory(clss)


def dump_info():
    import json
    import os
    from .preference import get_pref
    if "--get-blender-ai-node-info" in sys.argv:
        model_path = getattr(get_pref(), 'model_path')
        info = {"Version": ".".join([str(i) for i in bl_info["version"]]), "ComfyUIPath": model_path}
        sys.stderr.write(f"BlenderComfyUIInfo: {json.dumps(info)} BlenderComfyUIend")
        sys.stderr.flush()
        print(f'Blender {os.getpid()} PID', file=sys.stderr)


def track_ae():
    mod = sys.modules.get(__package__, None)
    if mod:
        __dict__["__addon_enabled__"] = False
    return 1


def disable_reload():
    for nmod in sys.modules:
        if nmod == __package__ or not nmod.startswith(__package__):
            continue
        mod = sys.modules[nmod]
        if not hasattr(mod, "__addon_enabled__"):
            mod.__addon_enabled__ = False
    if bpy.app.timers.is_registered(track_ae):
        return
    bpy.app.timers.register(track_ae, persistent=True)
    # reset disable
    _disable = disable
    def hd(mod, *, default_set=False, handle_error=None):
        if default_set and mod == __package__:
            __dict__["NOT_RELOAD_BUILTIN"] = True
        _disable(mod, default_set=default_set, handle_error=handle_error)
        if default_set and mod == __package__:
            __dict__.pop("NOT_RELOAD_BUILTIN")
    sys.modules["addon_utils"].disable = hd

def reload_builtin():
    if "NOT_RELOAD_BUILTIN" in __dict__:
        return False
    return __dict__.get("__addon_enabled__", None) is False


def register():
    if reload_builtin():
        return
    _ = ScopeTimer(f"{__package__} Register")
    reg_tracker()
    pref_register()
    if bpy.app.background:
        dump_info()
        return
    bpy.app.translations.register(__name__, translations_dict)
    reg()
    Icon.set_hq_preview()
    TaskManager.run_server(fake=True)
    timer_reg()
    bpy.types.Scene.sdn = bpy.props.PointerProperty(type=Prop)
    bpy.types.Scene.sdn_history_item = bpy.props.CollectionProperty(type=HistoryItem)
    bpy.types.Scene.sdn_history_item_index = bpy.props.IntProperty(default=0)
    History.register_timer()
    linker_register()
    use_hook()
    FSWatcher.init()
    disable_reload()
    print(f"{__package__} Launch Time: {time.time() - ts:.4f}s")


def unregister():
    if reload_builtin():
        return
    unreg_tracker()
    pref_unregister()
    if bpy.app.background:
        return
    bpy.app.translations.unregister(__name__)
    unreg()
    rtnode_unreg()
    timer_unreg()
    del bpy.types.Scene.sdn
    del bpy.types.Scene.sdn_history_item
    del bpy.types.Scene.sdn_history_item_index
    modules_update()
    linker_unregister()
    use_hook(False)
    FSWatcher.stop()


def modules_update():
    from .kclogger import close_logger
    close_logger()
    import sys
    modules = []
    for i in sys.modules.keys():
        if i.startswith(__package__) and i != __package__:
            modules.append(i)
    for i in modules:
        del sys.modules[i]
    del sys.modules[__package__]
