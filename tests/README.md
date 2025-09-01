# 测试说明

这个目录包含了Claude限流监控系统的所有测试文件。

## 测试文件说明

- `test_integration.py` - 集成测试，验证完整的监控流程
- `test_status_change.py` - 状态变化检测测试
- `test_system.py` - 系统组件测试

## 运行测试

### 运行单个测试
```bash
# 运行集成测试
python3 tests/test_integration.py

# 运行状态变化测试
python3 tests/test_status_change.py

# 运行系统测试
python3 tests/test_system.py
```

### 运行所有测试
```bash
# 从项目根目录运行
python3 -m pytest tests/ -v

# 或者直接运行
for test in tests/test_*.py; do
    echo "Running $test..."
    python3 "$test"
    echo ""
done
```

## 测试覆盖

- ✅ 状态变化检测功能
- ✅ 首次运行场景
- ✅ 无状态变化场景
- ✅ 批量通知功能
- ✅ 错误处理
- ✅ 配置文件加载
- ✅ 飞书通知器集成

## 注意事项

- 测试文件会创建临时文件用于测试，请确保有写入权限
- 测试完成后会自动清理临时文件
- 飞书通知测试使用测试webhook，不会真的发送消息
