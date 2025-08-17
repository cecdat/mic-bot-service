// 增强版账户状态切换测试脚本 - 完整流程记录
console.log('[测试脚本] 已加载，开始记录状态切换完整流程');

// 添加测试按钮到页面
function addTestButton() {
  console.log('[测试脚本] 添加测试按钮');
  const button = document.createElement('button');
  button.textContent = '测试状态切换';
  button.style.margin = '10px';
  button.style.padding = '5px 10px';
  button.style.backgroundColor = '#1E9FFF';
  button.style.color = 'white';
  button.style.border = 'none';
  button.style.borderRadius = '4px';
  button.style.cursor = 'pointer';
  
  button.addEventListener('click', function() {
    console.log('[测试脚本] 测试按钮被点击');
    const statusSwitch = document.querySelector('.account-status-switch');
    if (statusSwitch) {
      console.log('[测试脚本] 找到状态开关元素:', statusSwitch);
      console.log('[测试脚本] 账户ID:', statusSwitch.dataset.id);
      console.log('[测试脚本] 当前状态:', statusSwitch.checked ? '启用' : '禁用');
      
      // 触发点击事件
      statusSwitch.click();
      console.log('[测试脚本] 点击后状态:', statusSwitch.checked ? '启用' : '禁用');
    } else {
      console.error('[测试脚本] 未找到状态开关元素');
    }
  });
  
  // 将按钮添加到页面
  const container = document.querySelector('body');
  if (container) {
    container.appendChild(button);
    console.log('[测试脚本] 测试按钮已添加到页面');
  } else {
    console.error('[测试脚本] 未找到添加按钮的容器');
  }
}

// 页面加载完成后添加测试按钮
window.addEventListener('load', function() {
  console.log('[测试脚本] 页面加载完成');
  addTestButton();
});

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
  console.log('[测试脚本] DOM已加载完成');
  
  // 查找状态开关元素
  setTimeout(function() {
    const statusSwitch = document.querySelector('.account-status-switch');
    if (statusSwitch) {
      console.log('[测试脚本] 找到状态开关元素:', statusSwitch);
      console.log('[测试脚本] 账户ID:', statusSwitch.dataset.id);
      console.log('[测试脚本] 当前状态:', statusSwitch.checked ? '启用' : '禁用');
      
      // 测试事件监听器
      testEventListeners(statusSwitch);
      
      // 手动触发点击事件
      testClickEvent(statusSwitch);
      
      // 测试直接调用toggleAccountStatus函数
      testToggleFunction(statusSwitch);
    } else {
      console.error('[测试脚本] 未找到状态开关元素');
    }
  }, 1000);
});

// 测试事件监听器 - 增强版
function testEventListeners(element) {
  console.log('[测试脚本] 开始详细检查事件监听器...');
  try {
    // 元素基本信息
    console.log('[测试脚本] 元素类型:', element.tagName);
    console.log('[测试脚本] 元素ID:', element.id);
    console.log('[测试脚本] 元素类名:', element.className);
    console.log('[测试脚本] 元素data-id:', element.dataset.id);
    console.log('[测试脚本] 元素checked状态:', element.checked);
    console.log('[测试脚本] 元素disabled状态:', element.disabled);
    
    // 检查元素上的onchange属性
    console.log('\n[测试脚本] 检查onchange属性事件处理器:');
    if (element.onchange) {
      console.log('[测试脚本] ✅ 存在onchange属性事件处理器');
      console.log('[测试脚本] 处理器代码:', element.onchange.toString().substring(0, 200) + '...');
    } else {
      console.log('[测试脚本] ❌ 不存在onchange属性事件处理器');
    }
    
    // 尝试检查通过addEventListener添加的事件监听器
    console.log('\n[测试脚本] 检查通过addEventListener添加的事件监听器:');
    if (typeof getEventListeners === 'function') {
      const events = getEventListeners(element);
      console.log('[测试脚本] 元素上注册的事件类型:', Object.keys(events).join(', '));
      
      if (events.change && events.change.length > 0) {
        console.log('[测试脚本] ✅ 存在', events.change.length, '个change事件监听器');
        events.change.forEach((listener, index) => {
          console.log(`[测试脚本] 监听器${index+1}:`);
          console.log(`[测试脚本]   - 类型: ${listener.type}`);
          console.log(`[测试脚本]   - 捕获: ${listener.capture}`);
          console.log(`[测试脚本]   - 被动: ${listener.passive}`);
          console.log(`[测试脚本]   - 代码: ${listener.listener.toString().substring(0, 200) + '...'}`);
        });
      } else {
        console.log('[测试脚本] ❌ 不存在通过addEventListener添加的change事件监听器');
      }
    } else {
      console.log('[测试脚本] ℹ️ getEventListeners函数不可用，无法检查通过addEventListener添加的事件监听器');
      console.log('[测试脚本] ℹ️ 请在Chrome开发者工具中使用getEventListeners(element)手动检查');
    }
    
    // 检查父元素是否有事件委托
    console.log('\n[测试脚本] 检查父元素事件委托:');
    let parent = element.parentElement;
    let depth = 0;
    const maxDepth = 5;
    
    while (parent && depth < maxDepth) {
      console.log(`[测试脚本] 父元素${depth+1} (${parent.tagName}):`);
      if (typeof getEventListeners === 'function') {
        const parentEvents = getEventListeners(parent);
        if (parentEvents.change && parentEvents.change.length > 0) {
          console.log(`[测试脚本] ✅ 父元素${depth+1}上存在${parentEvents.change.length}个change事件监听器 (可能是事件委托)`);
        } else {
          console.log(`[测试脚本] ❌ 父元素${depth+1}上不存在change事件监听器`);
        }
      }
      parent = parent.parentElement;
      depth++;
    }
  } catch (e) {
    console.error('[测试脚本] 检查事件监听器时出错:', e);
    console.error('[测试脚本] 错误详情:', e.stack);
  }
  console.log('[测试脚本] 事件监听器检查完成\n');
}

// 测试点击事件 - 增强版
function testClickEvent(element) {
  console.log('[测试脚本] 开始测试点击事件...');
  try {
    const initialState = element.checked;
    const timestampBefore = new Date().toISOString();
    console.log(`[测试脚本] 点击前 [${timestampBefore}]`);
    console.log('[测试脚本] 初始状态:', initialState ? '启用' : '禁用');
    console.log('[测试脚本] 元素ID:', element.id);
    console.log('[测试脚本] 元素data-id:', element.dataset.id);
    
    // 记录点击前的事件监听器状态
    testEventListeners(element);
    
    // 创建并触发点击事件
    console.log('[测试脚本] 触发点击事件...');
    const event = new MouseEvent('click', { bubbles: true, cancelable: true });
    const isDispatched = element.dispatchEvent(event);
    console.log('[测试脚本] 事件是否成功调度:', isDispatched);
    
    // 验证状态是否变化
    setTimeout(() => {
      const finalState = element.checked;
      const timestampAfter = new Date().toISOString();
      console.log(`[测试脚本] 点击后 [${timestampAfter}]`);
      console.log('[测试脚本] 点击后状态:', finalState ? '启用' : '禁用');
      
      if (finalState !== initialState) {
        console.log('[测试脚本] ✅ 点击事件成功触发，状态已变化');
        console.log('[测试脚本] 状态变化: 从', initialState ? '启用' : '禁用', '变为', finalState ? '启用' : '禁用');
      } else {
        console.log('[测试脚本] ❌ 点击事件触发后状态未变化');
        console.log('[测试脚本] 当前状态仍为:', finalState ? '启用' : '禁用');
        // 再次检查事件监听器
        console.log('[测试脚本] 重新检查事件监听器:');
        testEventListeners(element);
      }
    }, 1000); // 增加延迟时间以便观察异步更新
  } catch (e) {
    console.error('[测试脚本] 测试点击事件时出错:', e);
    console.error('[测试脚本] 错误详情:', e.stack);
  }
}

// 测试直接调用toggleAccountStatus函数 - 增强版
function testToggleFunction(element) {
  console.log('[测试脚本] 开始测试toggleAccountStatus函数...');
  try {
    const timestampStart = new Date().toISOString();
    console.log(`[测试脚本] 操作开始 [${timestampStart}]`);
    
    const accountId = parseInt(element.dataset.id);
    const email = element.dataset.email;
    const isEnabled = element.checked;
    const action = !isEnabled ? 'enable' : 'disable'; // 注意：后端API可能需要英文action
    const actionText = !isEnabled ? '启用' : '禁用';
    
    console.log('[测试脚本] 用户ID:', accountId);
    console.log('[测试脚本] 邮箱:', email);
    console.log('[测试脚本] 当前状态:', isEnabled ? '启用' : '禁用');
    console.log('[测试脚本] 操作类型:', action);
    console.log('[测试脚本] 操作描述:', actionText);
    
    if (typeof toggleAccountStatus === 'function') {
      console.log('[测试脚本] ✅ toggleAccountStatus函数存在');
      console.log('[测试脚本] 函数定义:', toggleAccountStatus.toString().substring(0, 300) + '...');
      
      // 记录函数调用前的时间
      const startTime = performance.now();
      console.log('[测试脚本] 调用toggleAccountStatus函数...');
      
      try {
        // 调用函数并捕获返回值
        const result = toggleAccountStatus(accountId, action);
        const endTime = performance.now();
        console.log(`[测试脚本] 函数调用完成，耗时: ${(endTime - startTime).toFixed(2)}ms`);
        console.log('[测试脚本] 函数返回值:', result);
      } catch (funcError) {
        console.error('[测试脚本] 调用toggleAccountStatus函数时出错:', funcError);
        console.error('[测试脚本] 错误详情:', funcError.stack);
        console.log('[测试脚本] 尝试直接发送请求...');
        sendToggleRequest(accountId, action);
      }
    } else {
      console.log('[测试脚本] ❌ toggleAccountStatus函数不存在');
      console.log('[测试脚本] 尝试直接发送请求...');
      sendToggleRequest(accountId, action);
    }
  } catch (e) {
    console.error('[测试脚本] 测试toggleAccountStatus函数时出错:', e);
    console.error('[测试脚本] 错误详情:', e.stack);
  }
}
    }, 1000);
  }
}

// 直接发送切换请求
function sendToggleRequest(accountId) {
  console.log(`[测试脚本] 直接发送切换请求到/web_api/bot_accounts/${accountId}/toggle`);
  
  if (typeof fetchWithAuth === 'function') {
    fetchWithAuth(`/web_api/bot_accounts/${accountId}/toggle`, {
      method: 'POST'
    })
    .then(res => {
      console.log('[测试脚本] 请求状态:', res.status);
      return res.json();
    })
    .then(data => {
      console.log('[测试脚本] 请求结果:', data);
      if (data.status === 'success') {
        console.log('[测试脚本] 切换成功，新状态:', data.is_enabled);
        // 尝试更新UI
        updateStatusSwitch(accountId, data.is_enabled);
      }
    })
    .catch(error => {
      console.error('[测试脚本] 请求失败:', error);
    });
  } else {
    console.error('[测试脚本] fetchWithAuth函数不存在');
  }
}

// 更新状态开关UI
function updateStatusSwitch(accountId, isEnabled) {
  console.log(`[测试脚本] 尝试更新账户ID ${accountId} 的状态开关UI为: ${isEnabled ? '启用' : '禁用'}`);
  
  const statusSwitch = document.querySelector(`.account-status-switch[data-id="${accountId}"]`);
  if (statusSwitch) {
    statusSwitch.checked = isEnabled;
    console.log('[测试脚本] 状态开关UI已更新');
  } else {
    console.error('[测试脚本] 未找到对应账户的状态开关元素');
  }
}