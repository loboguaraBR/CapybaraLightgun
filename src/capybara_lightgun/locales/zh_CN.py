"""中文（简体） — textos longos e traduções da interface."""
# flake8: noqa

T = {'"Still" threshold (°/s)': '"静止"阈值（°/s）',
 '1.00 = real gun: the aim follows the barrel exactly. Above 1, a smaller movement covers the screen.': '1.00 = '
                                                                                                        '真实枪械：准星完全跟随枪管。大于 '
                                                                                                        '1 '
                                                                                                        '时，较小的动作即可覆盖整个屏幕。',
 '<b>Emulators:</b> RetroArch → Input → Device type <i>Light Gun</i>; MAME → <code>-lightgun -lightgun_device mouse</code>. PC games without absolute mouse support → <i>Gyro mouse</i> mode.': '<b>模拟器：</b>RetroArch '
                                                                                                                                                                                                '→ '
                                                                                                                                                                                                '输入 '
                                                                                                                                                                                                '→ '
                                                                                                                                                                                                '设备类型 '
                                                                                                                                                                                                '<i>Light '
                                                                                                                                                                                                'Gun</i>；MAME '
                                                                                                                                                                                                '→ '
                                                                                                                                                                                                '<code>-lightgun '
                                                                                                                                                                                                '-lightgun_device '
                                                                                                                                                                                                'mouse</code>。不支持绝对鼠标的 '
                                                                                                                                                                                                'PC '
                                                                                                                                                                                                '游戏 '
                                                                                                                                                                                                '→ '
                                                                                                                                                                                                '<i>陀螺仪鼠标</i>模式。',
 '<b>Light gun only (driver)</b>: the cursor and touchpad stay free; RetroArch (<i>udev</i> input driver) uses the gun. <b>System mouse</b>: the gun moves the cursor; moving the touchpad makes it yield for a few seconds. <b>HOME</b> on the controller pauses the aim. Recenter: point at the <b>center</b> of the screen and press <b>Y</b>.': '<b>仅光枪（驱动）</b>：光标和触控板保持自由；RetroArch（<i>udev</i> '
                                                                                                                                                                                                                                                                                                                                                    '输入驱动）使用光枪。<b>系统鼠标</b>：光枪移动光标；动一下触控板会让光枪让出光标几秒。手柄上的 '
                                                                                                                                                                                                                                                                                                                                                    '<b>HOME</b> '
                                                                                                                                                                                                                                                                                                                                                    '暂停瞄准。重新居中：对准屏幕<b>中心</b>并按 '
                                                                                                                                                                                                                                                                                                                                                    '<b>Y</b>。',
 '@help': '\n'
          '<h3>入门</h3>\n'
          '<ol>\n'
          '<li>将手柄静置约 1 秒（陀螺仪显示 <b>正常</b>）。</li>\n'
          '<li><b>校准</b>：按游戏时的姿势握持，依次对准屏幕中心和 4 个角并扣动扳机。</li>\n'
          '<li>游戏中如果准星向侧面漂移：对准屏幕<b>中心</b>并按 <b>Y</b>（PlayStation 上为 □）。</li>\n'
          '</ol>\n'
          '<h3>使用哪种模式</h3>\n'
          '<ul>\n'
          '<li><b>仅光枪（驱动）</b> — 光标和触控板保持自由。<b>RetroArch</b>：设置 → 驱动 → 输入 = <i>udev</i>；\n'
          '输入 → 端口 1 → 设备类型 = <i>Light Gun</i>，鼠标索引 = <i>Capybara Lightgun (driver)</i>。\n'
          '绑定 <i>Gun Trigger</i>、<i>Gun Reload</i>（aux A = 右键）和 <i>Gun Start/Select</i>。</li>\n'
          '<li><b>系统鼠标</b> — 适用于一切：<b>MAME</b>（<code>-lightgun -lightgun_device mouse</code>，\n'
          '配合 <code>-offscreen_reload</code>）、<b>Dolphin</b>（Wii：指针 = 鼠标）、<b>DuckStation/PCSX2</b>（GunCon = 鼠标）、\n'
          '用鼠标瞄准的 PC 游戏。</li>\n'
          '<li><b>陀螺仪鼠标</b>（输出页 → 瞄准模式）— 用于不支持绝对鼠标的 PC 射击游戏。</li>\n'
          '</ul>\n'
          '<h3>精度技巧</h3>\n'
          '<ul>\n'
          '<li>请<b>在实际游戏的位置</b>校准（坐/站、距离）。换了位置？重新校准。</li>\n'
          '<li>静止时抖动：调低<i>静止稳定度</i>（如 0.8）或开启<i>微动锁定</i>。</li>\n'
          '<li>快速转动时滞后：调高<i>快速移动响应</i>。</li>\n'
          '<li>光标一顿一顿：调高<i>运动平滑度</i>（20–25 毫秒）。有延迟：调低（8–10 毫秒）。</li>\n'
          '<li>扣扳机时弹着点偏移：调高<i>扳机抖动补偿</i>（35–50 毫秒）。</li>\n'
          '<li>弹着点总是偏向一侧：使用<i>微调</i>（瞄具）。</li>\n'
          '<li>缓慢漂移：关卡之间把手柄放在桌上 — 陀螺仪会自动重新校准。</li>\n'
          '</ul>\n'
          '<h3>装弹</h3>\n'
          '<ul>\n'
          '<li>使用 <b>R</b>/<b>R1</b>，或在"手柄"页开启<i>对准屏幕外装弹</i>（像真枪一样对准屏幕外射击）或<i>甩动装弹</i>。</li>\n'
          '</ul>\n'
          '<h3>其他手柄</h3>\n'
          '<ul>\n'
          '<li><b>DualSense（PS5）/ DualShock 4（PS4）</b>：通过蓝牙或 USB 配对；用<b>手柄正面</b>（灯条）对准屏幕。\n'
          'R2 = 扳机，R1 = 装弹，□ = 重新居中。</li>\n'
          '<li><b>其他带陀螺仪的手柄</b>（Steam Deck/Controller、8BitDo 等）：来源选择<i>其他带陀螺仪的手柄</i>。正面朝向屏幕握持。</li>\n'
          '<li><b>没有带陀螺仪的手柄</b>（例如 Xbox 手柄）：使用<i>系统鼠标</i>来源（或预设配置）。鼠标仍是鼠标，应用会加上光枪功能：\n'
          '装弹（右键 = 屏幕外射击）、连发、按键、屏幕准星和配置。在驱动模式（Linux）下，鼠标也会驱动虚拟光枪。</li>\n'
          '</ul>\n'
          '<h3>自动配置</h3>\n'
          '<p>在"配置"页中输入游戏窗口名称里的词（例如 <code>retroarch</code>、<code>mame</code>）。游戏处于前台时会自动启用该配置。</p>\n'
          '<h3>语言</h3>\n'
          '<p>顶部（以及托盘菜单）的 <b>🌐 Language</b> 选择器始终显示英文，误选语言时可以轻松切回 English。</p>\n'
          '<h3>macOS</h3>\n'
          '<p>在 <b>系统设置 → 隐私与安全性</b> 中允许本应用：<b>辅助功能</b>（移动光标和点击）和<b>输入监控</b>（读取手柄）。\n'
          '"实时"栏中的黄色按钮会打开这些页面。Mac 上只有<i>系统鼠标</i>模式。</p>\n'
          '<h3>蓝牙</h3>\n'
          '<p>笔记本的蓝牙与 Wi-Fi 共用无线模块：如果瞄准偶尔卡顿，请优先使用 5 GHz Wi-Fi、让手柄靠近，或使用 USB 蓝牙适配器。</p>\n',
 'A button outside the list (raw Linux name, e.g. BTN_TR2) shows up here by itself when you press it.': '列表外的按键（Linux '
                                                                                                        '原始名称，例如 '
                                                                                                        'BTN_TR2）在你按下时会自动出现在这里。',
 'A strong jerk of the gun (downwards, like pumping a shotgun) fires an off-screen shot.': '用力向下甩一下枪（像给霰弹枪上膛）会触发一次屏幕外射击。',
 'Above this acceleration, the accelerometer is ignored.': '超过此加速度时忽略加速度计。',
 'Accessibility': '辅助功能',
 'Activate "{name}" automatically': '自动启用"{name}"',
 'Aim': '瞄准',
 'Aim mode': '瞄准模式',
 'Aim source': '瞄准来源',
 'Aim too far off (pointing sideways). Try again.': '偏离太远（指向侧面）。请重试。',
 'Anti-tremor filter': '防抖滤波',
 'Auto-fire': '连发',
 'Auto-fire (shots/s)': '连发（发/秒）',
 'Automatic (any controller with a gyroscope)': '自动（任何带陀螺仪的手柄）',
 'Automatic drift correction': '自动漂移校正',
 'BOTTOM-LEFT corner': '左下角',
 'BOTTOM-RIGHT corner': '右下角',
 'Bluetooth delivers readings in bursts and sometimes stalls; this keeps the cursor moving at a steady pace. Higher = smoother but slightly more delayed. 0 = off (the cursor jumps).': '蓝牙会成批发送读数，有时还会卡顿；此项让光标保持匀速移动。越高越平滑，但延迟略大。0 '
                                                                                                                                                                                        '= '
                                                                                                                                                                                        '关闭（光标会跳动）。',
 'Bottom-left corner': '左下角',
 'Bottom-right corner': '右下角',
 'Buttons': '按键',
 'CENTER of the screen': '屏幕中心',
 'CROSSHAIR HIDDEN': '准星已隐藏',
 'Calibrate': '校准',
 'Calibrated! error {pct}% of the screen ({quality})': '校准完成！误差为屏幕的 {pct}%（{quality}）',
 'Calibrate…': '校准…',
 'Calibration': '校准',
 'Calibration {step}/{total}: aim at the {label} and pull the trigger': '校准 {step}/{total}：瞄准{label}并扣动扳机',
 'Capture · touchpad': '截图 · 触控板',
 'Controller': '手柄',
 'Controller connected: {name}': '手柄已连接：{name}',
 'Controller disconnected': '手柄已断开',
 'Create': '创建',
 'Crosshair': '屏幕准星',
 'Cursor update rate (Hz)': '光标刷新率（Hz）',
 'Default (light gun)': '默认（光枪）',
 'Delete': '删除',
 'Delete calibration': '删除校准',
 'Delete profile': '删除配置',
 'Delete the profile "{name}"?': '删除配置"{name}"？',
 'Delete the saved calibration?': '删除已保存的校准？',
 'Disconnected ({error})': '已断开（{error}）',
 'Distance to the screen (m)': '到屏幕的距离（米）',
 'Draws a crosshair on top of everything, where the gun points. Useful in driver mode for games that don\'t show one (shortcut: top button or the "Show/hide on-screen crosshair" action).': '在所有内容之上绘制准星，位置即枪口所指。适用于驱动模式下不显示准星的游戏（快捷方式：顶部按钮或"显示/隐藏屏幕准星"动作）。',
 'Draws the crosshair on top of everything, where the gun points.': '在所有内容之上绘制准星，位置即枪口所指。',
 'Duplicate': '复制',
 'Duplicate profile': '复制配置',
 'Error opening the controller: {error}': '打开手柄出错：{error}',
 'Error: {error}': '错误：{error}',
 'File: {path}': '文件：{path}',
 'Fraction of the desktop where the aim works (x0, y0, x1, y1). With 2 monitors side by side, the left one is 0 · 0 · 0.5 · 1.': '瞄准作用的桌面区域比例（x0, '
                                                                                                                                 'y0, '
                                                                                                                                 'x1, '
                                                                                                                                 'y1）。两台显示器并排时，左边那台为 '
                                                                                                                                 '0 '
                                                                                                                                 '· '
                                                                                                                                 '0 '
                                                                                                                                 '· '
                                                                                                                                 '0.5 '
                                                                                                                                 '· '
                                                                                                                                 '1。',
 'Freeze aim after the shot (ms)': '射击后冻结瞄准（毫秒）',
 'Game name': '游戏名称',
 'Games stop seeing the controller as a gamepad (avoids duplicate commands). Applies on reconnect.': '游戏不再把手柄识别为游戏手柄（避免重复指令）。重新连接后生效。',
 'Grant macOS permissions': '授予 macOS 权限',
 'Gravity correction': '重力校正',
 'Gun sight: shifts the point of impact if shots always land slightly to one side.': '瞄具微调：若弹着点总是偏向一侧，可平移命中点。',
 'Gyro mouse (PC/FPS)': '陀螺仪鼠标（PC/FPS）',
 'Gyro mouse (relative)': '陀螺仪鼠标（相对）',
 'Gyro mouse speed': '陀螺仪鼠标速度',
 'Gyroscope': '陀螺仪',
 'H hide crosshair · N reset · ESC exit': 'H 隐藏准星 · N 重置 · ESC 退出',
 'Help': '帮助',
 'Hide the controller from games': '对游戏隐藏手柄',
 'Higher = less lag on fast turns. Frantic games: raise it. Target shooting: lower it.': '越高，快速转动时延迟越小。激烈游戏：调高。精准射击：调低。',
 'Holds the cursor still right after shooting.': '射击后立即保持光标不动。',
 'Horizontal fine adjustment': '水平微调',
 'Horizontal sensitivity': '水平灵敏度',
 'How far past the edge counts as outside. Increase it if you reload by accident near the edges.': '超出边缘多远算作屏幕外。如果在边缘附近误装弹，请调大。',
 'How fast the accelerometer corrects the tilt. Higher = less vertical drift, but feels jerks more.': '加速度计校正倾斜的速度。越高垂直漂移越少，但对抖动更敏感。',
 'How long the gun waits after the last touchpad/mouse movement.': '触控板/鼠标最后一次移动后光枪等待的时间。',
 'How many times per second the cursor is updated. 250 is great; raise it for 144 Hz+ monitors.': '每秒更新光标的次数。250 '
                                                                                                  '即可；144 Hz 以上显示器可调高。',
 "If drift isn't corrected with the controller on the table, increase it a little.": '如果手柄放在桌上时漂移没有被校正，请稍微调大。',
 'Ignores movements smaller than this. Helps with small targets. 0 = off.': '忽略小于此值的移动。有助于瞄准小目标。0 = 关闭。',
 'In System Settings → Privacy & Security, turn on "Capybara Lightgun" under:\n\n• Accessibility — so the gun can move the cursor and click\n• Input Monitoring — to read the controller in the background\n\nThen quit and open the app again.': '在 '
                                                                                                                                                                                                                                                  '系统设置 '
                                                                                                                                                                                                                                                  '→ '
                                                                                                                                                                                                                                                  '隐私与安全性 '
                                                                                                                                                                                                                                                  '中，为"Capybara '
                                                                                                                                                                                                                                                  'Lightgun"开启：\n'
                                                                                                                                                                                                                                                  '\n'
                                                                                                                                                                                                                                                  '• '
                                                                                                                                                                                                                                                  '辅助功能 '
                                                                                                                                                                                                                                                  '— '
                                                                                                                                                                                                                                                  '让光枪移动光标并点击\n'
                                                                                                                                                                                                                                                  '• '
                                                                                                                                                                                                                                                  '输入监控 '
                                                                                                                                                                                                                                                  '— '
                                                                                                                                                                                                                                                  '在后台读取手柄\n'
                                                                                                                                                                                                                                                  '\n'
                                                                                                                                                                                                                                                  '然后退出并重新打开应用。',
 'Input Monitoring': '输入监控',
 'Invalid points — starting over.': '点位无效 — 重新开始。',
 'Jerk strength (g)': '甩动力度（g）',
 'Jerk tolerance (g)': '抖动容差（g）',
 'Joy-Con/Pro Controller (the most precise), DualSense, DualShock 4, others with a gyroscope (Steam Deck/Controller, 8BitDo…) or the system mouse for those without a controller. Regular Xbox controllers have no gyroscope: use the mouse.': 'Joy-Con/Pro '
                                                                                                                                                                                                                                               '手柄（最精确）、DualSense、DualShock '
                                                                                                                                                                                                                                               '4、其他带陀螺仪的手柄（Steam '
                                                                                                                                                                                                                                               'Deck/Controller、8BitDo…），没有手柄时可用系统鼠标。普通 '
                                                                                                                                                                                                                                               'Xbox '
                                                                                                                                                                                                                                               '手柄没有陀螺仪：请使用鼠标。',
 'Keyboard key…': '键盘按键…',
 'Left click': '左键',
 'Light gun (absolute)': '光枪（绝对）',
 'Light gun only (driver)': '仅光枪（驱动）',
 'Light gun only (driver) — cursor free': '仅光枪（驱动）— 光标自由',
 'Light gun only (driver): the desktop ignores the gun; cursor and touchpad stay free and RetroArch (udev input driver) uses the gun. System mouse: the gun moves the cursor (works with any game, including MAME).': '仅光枪（驱动）：桌面忽略光枪；光标和触控板保持自由，RetroArch（udev '
                                                                                                                                                                                                                      '输入驱动）使用光枪。系统鼠标：光枪移动光标（适用于任何游戏，包括 '
                                                                                                                                                                                                                      'MAME）。',
 "Light gun: goes where the barrel points (emulators, shooting games). Gyro mouse: moves the regular mouse, for PC games that don't accept an absolute mouse.": '光枪：指向枪管所指之处（模拟器、射击游戏）。陀螺仪鼠标：移动普通鼠标，用于不支持绝对鼠标的 '
                                                                                                                                                                'PC '
                                                                                                                                                                '游戏。',
 'Light-gun-only (driver) mode exists only on Linux (Windows and macOS would need a system driver). Using the system mouse.': '"仅光枪"模式只在 '
                                                                                                                              'Linux '
                                                                                                                              '上可用（Windows '
                                                                                                                              '和 '
                                                                                                                              'macOS '
                                                                                                                              '需要系统驱动）。正在使用系统鼠标。',
 'Like a real light gun: point outside the screen and pull the trigger to reload.': '和真实光枪一样：对准屏幕外扣动扳机即可装弹。',
 'Linux only (Windows and macOS would need a system driver).': '仅限 Linux（Windows 和 macOS 需要系统驱动）。',
 'Live': '实时',
 'Longer = heavier recoil.': '越长后坐力越"重"。',
 'Looking for a controller…': '正在查找手柄…',
 'Lower = reloads with less force. If it reloads by itself when aiming fast, increase it.': '越低越容易装弹。若快速瞄准时自动装弹，请调高。',
 'Lower = steadier aim when still, but "heavier" in slow movements.': '越低静止时瞄准越稳，但慢速移动时更"沉"。',
 'MAME (-offscreen_reload)': 'MAME（-offscreen_reload）',
 'Measure gyroscope': '测量陀螺仪',
 'Measures the gyroscope error by itself whenever the controller rests still.': '手柄静止放置时自动测量陀螺仪误差。',
 'Micro-movement lock': '微动锁定',
 'Middle click': '中键',
 'Middle of the bottom edge': '底边中点',
 "Missing macOS permission: {names}. Without it the gun can't move the cursor / read the controller.": '缺少 macOS '
                                                                                                       '权限：{names}。没有它光枪无法移动光标/读取手柄。',
 'Mode': '模式',
 'Monitor': '显示器',
 'Monitor number (0, 1…). -1 = use the area above.': '显示器编号（0、1…）。-1 = 使用上面的区域。',
 'Motion smoothness (ms)': '运动平滑度（毫秒）',
 'Mouse left': '鼠标左键',
 'Mouse middle': '鼠标中键',
 'Mouse mode: if you move the touchpad or mouse, the gun releases the cursor for a few seconds (it comes back when you shoot).': '鼠标模式：动一下触控板或鼠标，光枪会让出光标几秒（射击时恢复）。',
 'Mouse right': '鼠标右键',
 'Mouse side 1': '鼠标侧键 1',
 'Mouse side 2': '鼠标侧键 2',
 'Name of the copy:': '副本名称：',
 'New name:': '新名称：',
 'New profile': '新配置',
 'Nintendo Switch (Joy-Con / Pro Controller)': 'Nintendo Switch（Joy-Con / Pro 手柄）',
 'No controller found. Connect a controller with a gyroscope or choose the system mouse.': '未找到手柄。请连接带陀螺仪的手柄，或选择系统鼠标。',
 'Off-screen margin': '屏幕外边距',
 'Off-screen shot (reload)': '屏幕外射击（装弹）',
 'Off-screen shot goes to': '屏幕外射击位置',
 'On-screen crosshair size (px)': '屏幕准星大小（像素）',
 'One profile per game or emulator. The active profile applies immediately; you can also switch with the selector at the top or the tray icon.': '每个游戏或模拟器一个配置。当前配置立即生效；也可以通过顶部选择器或托盘图标切换。',
 'Only used without calibration.': '仅在未校准时使用。',
 'Open panel': '打开面板',
 'Other controller with a gyroscope (SDL)': '其他带陀螺仪的手柄（SDL）',
 'Output': '输出',
 'Pause aim': '暂停瞄准',
 'Pause/resume aim': '暂停/恢复瞄准',
 'PlayStation (DualSense PS5 / DualShock 4)': 'PlayStation（DualSense PS5 / DualShock 4）',
 'PlayStation (DualSense/DS4)': 'PlayStation（DualSense/DS4）',
 'Positive = lower.': '正值 = 向下。',
 'Precision (target shooting)': '精准（打靶）',
 'Prediction during stalls (ms)': '卡顿时预测（毫秒）',
 'Press a button on the controller: its name lights up. Names: Switch · PlayStation. Mouse buttons apply when the aim source is the system mouse.': '按下手柄上的按键：其名称会亮起。名称：Switch '
                                                                                                                                                    '· '
                                                                                                                                                    'PlayStation。瞄准来源为系统鼠标时，鼠标按键生效。',
 'Profile': '配置',
 'Profile:': '配置：',
 'Profile: {name}': '配置：{name}',
 'Profiles': '配置',
 'Quit': '退出',
 'Rapid-fire arcade': '街机连射',
 'Recenter': '重新居中',
 'Recenter (aim at the center)': '重新居中（对准中心）',
 'Recenter aim': '准星居中',
 'Recoil (rumble on each shot)': '后坐力（每次射击震动）',
 'Recoil duration (ms)': '后坐力时长（毫秒）',
 'Recoil strength': '后坐力强度',
 'Reconnect': '重新连接',
 'Relative mode only.': '仅限相对模式。',
 'Reload by aiming off-screen': '对准屏幕外装弹',
 'Reload with a jerk': '甩动装弹',
 'Rename': '重命名',
 'Rename profile': '重命名配置',
 'Response to fast movements': '快速移动响应',
 'Resume aim': '恢复瞄准',
 'Right click': '右键',
 'Same as horizontal, for up/down.': '与水平相同，用于上下方向。',
 'Screen area': '屏幕区域',
 'Screen height (m)': '屏幕高度（米）',
 'Screen width (m)': '屏幕宽度（米）',
 'Sensor': '传感器',
 'Shooting': '射击',
 'Show crosshair on screen': '在屏幕上显示准星',
 'Show/hide on-screen crosshair': '显示/隐藏屏幕准星',
 'Speed of the "Auto-fire" action (map it in the Buttons tab).': '"连发"动作的速度（在"按键"页中映射）。',
 'Stability when still (Hz)': '静止稳定度（Hz）',
 'Still running here in the tray. Click the icon to open; right-click to quit.': '仍在托盘中运行。点击图标打开；右键退出。',
 'System mouse': '系统鼠标',
 'System mouse (no controller)': '系统鼠标（无手柄）',
 'TOP-LEFT corner': '左上角',
 'TOP-RIGHT corner': '右上角',
 'Test range': '测试靶场',
 'Test range…': '测试靶场…',
 'The aim controls': '瞄准控制对象',
 'The desktop ignores the gun: cursor and touchpad stay free. Use it with RetroArch (udev input driver).': '桌面忽略光枪：光标和触控板保持自由。配合 '
                                                                                                           'RetroArch（udev '
                                                                                                           '输入驱动）使用。',
 'The gun moves the system cursor. Works with any game. Moving the touchpad makes the gun yield the cursor for a few seconds.': '光枪移动系统光标。适用于任何游戏。动一下触控板会让光枪让出光标几秒。',
 "The shot uses the position from X ms before the press, so the finger's jerk doesn't throw off the aim.": '射击使用按下前 X '
                                                                                                           '毫秒的位置，避免手指扣扳机的抖动影响瞄准。',
 "The system mouse doesn't need calibration.": '系统鼠标无需校准。',
 'Tip: keep the sensitivities at 1.00 so the aim is faithful to the barrel, like a real light gun. Change them only if the game requires it.': '提示：灵敏度保持 '
                                                                                                                                               '1.00，准星就会忠实跟随枪管，就像真正的光枪。仅在游戏需要时修改。',
 'Top-left corner': '左上角',
 'Top-right corner': '右上角',
 'Trigger (left click)': '扳机（左键）',
 'Trigger jerk compensation (ms)': '扳机抖动补偿（毫秒）',
 "Turn it off only to compare: the aim becomes raw, with your hand's tremor.": '仅用于对比时关闭：准星会变成原始数据，带有手部抖动。',
 'Use': '使用',
 'Vertical fine adjustment': '垂直微调',
 'Vertical sensitivity': '垂直灵敏度',
 "Vibrates the controller on every shot, like a gun's recoil. Joy-Con, Pro, DualSense and DS4.": '每次射击时手柄震动，模拟枪的后坐力。支持 '
                                                                                                 'Joy-Con、Pro、DualSense '
                                                                                                 '和 DS4。',
 'Vibration intensity.': '震动强度。',
 'When Bluetooth lags, keeps the movement going for up to this long instead of freezing.': '蓝牙延迟时，在此时长内继续推算移动而不是卡住。',
 'When the active window contains one of these words (comma-separated), this profile is activated; when you leave the game, it goes back to the profile you chose by hand. E.g.: retroarch, mame': '当活动窗口包含这些词之一（用逗号分隔）时启用此配置；离开游戏后恢复为手动选择的配置。例如：retroarch, '
                                                                                                                                                                                                   'mame',
 'Where the cursor goes to "shoot off-screen" (reload in many games).': '"屏幕外射击"时光标移动到的位置（许多游戏用来装弹）。',
 'Yield time (s)': '让出时间（秒）',
 'Yield to touchpad/mouse': '让位于触控板/鼠标',
 'active': '当前',
 'aim paused': '瞄准已暂停',
 'based on': '基于',
 'connected': '已连接',
 'console (simulation, mouse untouched)': '控制台（模拟，不动鼠标）',
 'good': '良好',
 'great': '优秀',
 'gyro mouse': '陀螺仪鼠标',
 'high — redo it aiming more calmly': '偏高 — 请更平稳地瞄准重做',
 "hold it the way you'll play · aim calmly · ESC cancels": '按游戏时的姿势握持 · 平稳瞄准 · ESC 取消',
 'light gun (absolute)': '光枪（绝对）',
 'light gun active': '光枪已启用',
 'macOS permissions': 'macOS 权限',
 'no controller': '无手柄',
 'none': '无',
 'none (test)': '无（测试）',
 'not calibrated (using screen size)': '未校准（使用屏幕尺寸）',
 'nothing': '无',
 'ok · error {pct}%': '正常 · 误差 {pct}%',
 'on': '开启',
 'paused': '已暂停',
 'rest the controller still for ~1 s': '将手柄静置约 1 秒',
 'saved': '已保存',
 'shots {shots} · hits {hits} · mean error {px} px ({pct}% of width)': '射击 {shots} · 命中 {hits} · 平均误差 {px} 像素（宽度的 '
                                                                       '{pct}%）',
 'system mouse (Quartz)': '系统鼠标（Quartz）',
 'system mouse (SendInput)': '系统鼠标（SendInput）',
 'system mouse (absolute)': '系统鼠标（绝对）',
 'virtual light gun (driver, cursor free)': '虚拟光枪（驱动，光标自由）',
 'yielding to touchpad': '正在让位于触控板',
 "{names}: no gyroscope (regular Xbox controllers don't have one). Use the system mouse.": '{names}：没有陀螺仪（普通 Xbox '
                                                                                           '手柄没有）。请使用系统鼠标。',
 '{name} (copy)': '{name}（副本）'}
