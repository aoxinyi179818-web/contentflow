ContentFlow AI 原型中文化插件

用途
将当前 ContentFlow AI Figma 原型中的主要界面文案改为简体中文，同时保留 ContentFlow、AI、H1/H2、版本号等必要英文标识。

输入
当前打开的 ContentFlow-AI-Prototype Figma Design 文件。

输出
1. 设计基础、组件、产品页面三个页面改为中文名称。
2. 四个核心产品页面的可见文案改为中文。
3. 本地文字样式切换为可用中文字体。
4. 原有组件、布局、颜色和原型跳转保持不变。

运行方法
1. 使用 Figma 桌面版打开 ContentFlow-AI-Prototype 文件。
2. 打开 Figma 菜单，选择 Plugins > Development > Import plugin from manifest。
3. 选择本目录下的 manifest.json。
4. 再次打开 Plugins > Development，运行“ContentFlow 中文化”。
5. 等待右下角出现“中文化完成”提示。

测试清单
1. 打开“02 产品页面”，确认四个画板标题均为中文。
2. 运行原型：新建内容 -> 工作流 -> 内容结果。
3. 点击历史记录，再点击“+ 新建内容”返回首页。
4. 检查大标题、按钮和表格是否出现截断或方框字。
5. 如果提示未找到中文字体，请安装 Noto Sans SC（思源黑体）后重启 Figma。

恢复方式
在运行插件后立即使用 Ctrl+Z；或者通过 Figma 的版本历史恢复运行前版本。
