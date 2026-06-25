# Splash Provider Gate Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复首屏启动时在缺少 chat 或 embedding provider 的情况下，欢迎页不退出、引导层被遮挡，导致用户看起来无法进入软件的问题。

**Architecture:** 保持现有 `splash -> workspace/settings` 三态结构不变，只修正 `App` 在 provider 检查失败时的状态切换顺序。通过先退出 `splash` 再展示引导层，避免被 `SplashScreen` 的固定定位和更高层级遮挡；同时补一条回归测试，锁定“缺配置时必须离开欢迎页”的行为。

**Tech Stack:** React 19、TypeScript、Vitest、Testing Library、framer-motion mock。

---

### Task 1: 为启动阻塞问题补回归测试

**Files:**
- Modify: `src/App.test.tsx`
- Test: `src/App.test.tsx`

- [ ] **Step 1: Write the failing test**

在 `src/App.test.tsx` 现有 “缺 chat 配置时弹引导” 用例附近新增一条更精确的回归测试，要求在缺少 provider 时欢迎页必须退出，且工作区已挂载，这样才能证明引导不会再被 `SplashScreen` 遮挡。

```tsx
  it("缺配置时退出欢迎页并显示工作区引导", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error("404"))
      .mockResolvedValueOnce({ id: "embed-1" });

    render(<App />);
    await act(async () => {
      vi.advanceTimersByTime(3800);
      await vi.runAllTicks();
    });

    expect(screen.queryByText("GreenBean Study Assistant")).toBeNull();
    expect(screen.getByText("我的文档")).toBeDefined();
    expect(screen.getByText(/尚未配置/)).toBeDefined();
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run: `rtk npm run test:frontend -- src/App.test.tsx`

Expected: 新增用例失败，表现为仍能查到 `GreenBean Study Assistant` 或查不到 `我的文档`，说明缺配置分支没有退出 `splash`。

- [ ] **Step 3: Keep existing adjacent behavior assertions**

保留现有这两个用例，不要删除：

```tsx
  it("缺 chat 配置时弹引导，确认后进入设置页", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error("404"))
      .mockResolvedValueOnce({ id: "embed-1" });

    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });

    expect(screen.getByText(/尚未配置/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /前往设置/ }));
    expect(screen.getByText("模型设置")).toBeDefined();
  });

  it("引导可关闭，暂不配置进入工作区", async () => {
    (getActiveProvider as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ id: "chat-1" })
      .mockRejectedValueOnce(new Error("404"));

    render(<App />);
    await act(async () => { vi.advanceTimersByTime(3800); await vi.runAllTicks(); });

    expect(screen.getByText(/尚未配置/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /稍后再说/ }));
    expect(screen.getByText("我的文档")).toBeDefined();
  });
```

这样可以确保修复不会破坏现有“去设置”和“稍后再说”的分支。

- [ ] **Step 4: Run the focused test file again before implementation review**

Run: `rtk npm run test:frontend -- src/App.test.tsx`

Expected: 仍然失败，但失败点应聚焦在新增回归测试；其余相关用例保持原状，证明测试写对了而不是测试环境坏了。

- [ ] **Step 5: Commit**

```bash
git add src/App.test.tsx
git commit -m "test(app): cover splash exit when provider missing"
```

### Task 2: 修正缺 provider 时的视图切换

**Files:**
- Modify: `src/App.tsx`
- Test: `src/App.test.tsx`

- [ ] **Step 1: Write the minimal implementation**

只修改 `handleSplashDone` 的失败分支，在显示引导前先切换到 `workspace`。不要改 `SplashScreen` 层级，不要新增状态字段，不要改后端接口语义。

```tsx
  const handleSplashDone = useCallback(() => {
    void Promise.allSettled([
      getActiveProvider("chat"),
      getActiveProvider("embedding"),
    ]).then((results) => {
      const missing = results.some((r) => r.status === "rejected");
      if (missing) {
        setView("workspace");
        setShowGuide(true);
      } else {
        setView("workspace");
      }
    });
  }, []);
```

这个实现的边界很明确：

```tsx
      if (missing) {
        setView("workspace");
        setShowGuide(true);
      }
```

修复点只在这里，因为 `SplashScreen` 是否显示完全由 `view === "splash"` 控制。

- [ ] **Step 2: Run test to verify it passes**

Run: `rtk npm run test:frontend -- src/App.test.tsx`

Expected: 新增回归测试通过，原有 App 级测试全部通过。

- [ ] **Step 3: Refactor only if duplication is obvious**

如果你想顺手消掉两个分支都写 `setView("workspace")` 的重复，只允许做一个不改行为的小重排，例如：

```tsx
  const handleSplashDone = useCallback(() => {
    void Promise.allSettled([
      getActiveProvider("chat"),
      getActiveProvider("embedding"),
    ]).then((results) => {
      const missing = results.some((r) => r.status === "rejected");
      setView("workspace");
      if (missing) {
        setShowGuide(true);
      }
    });
  }, []);
```

只在 focused tests 已经变绿后再做；如果做了，必须再次跑同一组测试确认无回归。

- [ ] **Step 4: Run the same tests again after optional refactor**

Run: `rtk npm run test:frontend -- src/App.test.tsx`

Expected: PASS，且输出中不应出现新的报错或 warning。

- [ ] **Step 5: Commit**

```bash
git add src/App.tsx src/App.test.tsx
git commit -m "fix(app): exit splash before provider setup guide"
```

### Task 3: 做最小范围验证并整理交付说明

**Files:**
- Modify: `src/App.tsx`
- Modify: `src/App.test.tsx`

- [ ] **Step 1: Run the nearest broader frontend test scope**

Run: `rtk npm run test:frontend -- src/App.test.tsx src/features/settings/pages/SettingsPage.test.tsx`

Expected: PASS，证明 App 启动流程修复没有破坏设置页相关交互。

- [ ] **Step 2: Inspect final diff briefly**

Run: `git diff --stat`

Expected: 只看到 `src/App.tsx` 与 `src/App.test.tsx` 的小范围变更；如果出现额外文件，先确认是否与本任务有关。

- [ ] **Step 3: Prepare concise handoff notes**

交付说明应覆盖这三点：

```text
1. 根因：缺 provider 时只显示引导、不退出 splash，导致引导层被欢迎页遮挡。
2. 修复：provider 检查失败时先切到 workspace，再显示引导。
3. 验证：App 启动相关测试与 settings 邻近测试通过。
```

- [ ] **Step 4: Optional manual verification command**

Run: `npm run dev`

Expected: 手动观察启动动画结束后，在缺 provider 场景下能看到工作区和引导，而不是继续停在欢迎页。

说明：这是可选人工验证，不阻塞代码交付；如果当前会话不适合长时间挂开发服务，可以只在交付说明中建议用户自行确认。

- [ ] **Step 5: Commit**

```bash
git add src/App.tsx src/App.test.tsx
git commit -m "test(app): verify splash provider gate fix"
```
