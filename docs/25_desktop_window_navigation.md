# Desktop window navigation / 桌面窗口导航

## English

Previously, the hidden assisted-export and beacon pages imposed their minimum size
on every page. The main window could grow to 1618×1031 in English or 1249×1032 in
Chinese even while showing a small page. The shared navigation now places each page
inside its own resizable scroll area. Long content scrolls inside the requested
window instead of expanding it. The application header stays outside the page scroll.

Use the page scrollbar or mouse wheel to reach later sections. Tab navigation and
programmatic keyboard focus reveal the focused control after layout has settled.
A queued focus update cannot scroll a page after it becomes hidden, and its timer
and signal connection are owned by the viewport so a language rebuild can destroy
them safely. Wide content retains horizontal scrolling as a fallback rather than
being silently clipped.

Existing page objects, navigation history, lifecycle checks and `on_enter` behavior
are retained. The viewport itself does not recreate pages, clear inputs, start work
or cancel background workers during ordinary navigation. Existing page-specific
reload behavior still applies. Language changes still use the existing shell rebuild;
this change does not add persistence for every unsaved draft across a rebuild.

Beacon and assisted-export consent controls retain their complete plain-text wording,
unchecked defaults, native checkbox role and explicit state changes. Their labels
wrap; keyboard Space and clicking the disclosure retain checkbox behavior. Scrolling,
resizing and focusing do not grant consent. All five existing export acknowledgements
remain required. The export buttons now occupy rows, with long actions spanning the
available width. Browser launch, export, beacon generation and disclosure logic are
unchanged; no action runs merely because its page is shown.

Status banners render literal text with word-boundary-or-anywhere wrapping. Long
unbroken folder names no longer widen the home page or lose trailing characters.
The same plain-text layout measures and paints the complete content; markup-like
characters remain literal, and no invisible separators are inserted into paths.

The navigation layer remains presentation-only. Synthetic checks cover hidden giant
pages, dynamic text reflow, focus visibility, per-page scroll/history behavior and
background-worker survival. Real MainWindow checks navigate every page in English
and Simplified Chinese at 940×700 and 1100×760, including focus on lower controls,
return navigation and language rebuilds. These sizes are Qt logical pixels; the
work does not establish all display scales, operating systems or assistive-technology
combinations. Current counts and package evidence are in
[CURRENT_STATUS.md](../CURRENT_STATUS.md).

No real vault, external browser session or AI model is needed for these checks.
This is a local usability repair, not a public release or new model validation.

## 中文版

此前，未显示的辅助导出页和信标页会把自身最小尺寸施加给所有页面。即使显示小页面，
主窗口也可能被撑到英文 1618×1031、中文 1249×1032。现在共享导航将每个页面放入独立、
可调整大小的滚动区域，长内容在指定窗口内滚动，不再撑大窗口。应用顶部栏位于页面
滚动区域之外。

使用页面滚动条或鼠标滚轮查看后续内容。Tab 导航及程序设置的键盘焦点会在布局完成后
显示对应控件。页面隐藏后，已排队的焦点更新不能再滚动它；定时器和信号连接由视口持有，
切换语言重建时可以安全销毁。确实很宽的内容仍可横向滚动，不会静默裁剪。

现有页面对象、导航历史、生命周期检查和 `on_enter` 行为均保留。普通导航过程中，视口
本身不会重建页面、清空输入、启动操作或取消后台任务；各页面已有的重新加载行为仍然
适用。语言切换继续使用现有外壳重建方式，本次不增加所有未保存草稿跨重建持久保存的能力。

信标与辅助导出的同意控件保留完整原文、默认不勾选、原生复选框角色及明确的状态变化。
文字可以换行，空格键与点击声明仍按复选框方式操作。滚动、调整大小及移动焦点不会
授予同意，导出的五项既有确认仍全部必需。导出按钮分行排列，长操作占用整行可用宽度。
浏览器启动、导出、信标生成和披露逻辑不变，仅显示页面不会执行这些操作。

状态栏按纯文本显示，优先在词边界换行，必要时可在词内折行。连续的超长文件夹名不再
撑宽主页或丢失末尾字符。测量和绘制共用完整纯文本布局；类似标记的字符仍按原文显示，
不会向路径插入不可见分隔符。

导航层仍只处理展示。合成检查覆盖隐藏的大页面、动态文字重排、焦点可见性、各页面滚动
与返回历史，以及后台任务存活。真实 MainWindow 检查在英文和简体中文下，以 940×700
及 1100×760 遍历所有页面，包含下方控件聚焦、返回导航和语言重建。这些尺寸为 Qt
逻辑像素；本轮不代表所有显示缩放、操作系统或辅助技术组合均已验证。最新测试数量和
打包证据见 [CURRENT_STATUS.md](../CURRENT_STATUS.md)。

上述检查不需要真实档案库、外部浏览器会话或 AI 模型。本轮属于本地可用性修复，不是
公开发布或新增模型验证。
