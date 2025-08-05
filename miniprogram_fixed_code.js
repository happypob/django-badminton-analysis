// index.js - 修复版小程序代码
Page({
  data: {
    deviceCode: '2025001', // 默认设备代码，与ESP32保持一致
    sessionId: '', // 当前会话ID
    isCollecting: false, // 是否正在采集
    serverUrl: 'http://47.122.129.159:8000' // 服务器地址
  },

  onLoad() {
    // 页面加载时检查是否有活跃会话
    const sessionId = wx.getStorageSync('session_id');
    if (sessionId) {
      this.setData({
        sessionId: sessionId,
        isCollecting: true
      });
      console.log('检测到活跃会话:', sessionId);
    }
  },

  // 设备代码输入处理
  onDeviceCodeInput(e) {
    this.setData({
      deviceCode: e.detail.value
    });
  },

  // 绑定设备按钮点击处理
  onBindDevice() {
    if (!this.data.deviceCode.trim()) {
      wx.showToast({ 
        title: '请输入设备代码', 
        icon: 'none' 
      });
      return;
    }
    
    this.bindDevice(this.data.deviceCode);
  },

  // 开始采集会话
  startSession() {
    console.log('开始采集会话...');
    
    // 检查是否已有活跃会话
    if (this.data.isCollecting) {
      wx.showToast({ 
        title: '已有活跃会话', 
        icon: 'none' 
      });
      return;
    }

    wx.request({
      url: `${this.data.serverUrl}/wxapp/start_session/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        openid: 'test_user_123456',
        device_group_code: this.data.deviceCode // 使用设备代码作为设备组编码
      },
      success: (res) => {
        console.log('开始会话响应:', res.data);
        
        if (res.statusCode === 200 && res.data.session_id) {
          // 保存会话ID到本地存储和页面数据
          const sessionId = res.data.session_id;
          wx.setStorageSync('session_id', sessionId);
          
          this.setData({
            sessionId: sessionId,
            isCollecting: true
          });
          
          wx.showToast({ 
            title: '会话开始成功', 
            icon: 'success' 
          });
          
          console.log('会话已开始，ID:', sessionId);
          console.log('ESP32需要轮询获取开始指令');
        } else {
          wx.showToast({ 
            title: res.data.error || '会话开始失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('开始会话失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 结束采集会话
  endSession() {
    console.log('结束采集会话...');
    
    const sessionId = this.data.sessionId || wx.getStorageSync('session_id');
    
    if (!sessionId) {
      wx.showToast({ 
        title: '没有活跃会话', 
        icon: 'none' 
      });
      return;
    }

    console.log('准备结束会话，ID:', sessionId);

    wx.request({
      url: `${this.data.serverUrl}/wxapp/end_session/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        session_id: sessionId
      },
      success: (res) => {
        console.log('结束会话响应:', res.data);
        
        if (res.statusCode === 200) {
          // 清除本地存储的会话ID和页面数据
          wx.removeStorageSync('session_id');
          this.setData({
            sessionId: '',
            isCollecting: false
          });
          
          wx.showToast({ 
            title: '会话结束成功', 
            icon: 'success' 
          });
          
          console.log('会话已结束，ESP32将收到停止指令');
        } else {
          wx.showToast({ 
            title: res.data.error || '会话结束失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('结束会话失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 绑定设备
  bindDevice(deviceCode) {
    console.log('绑定设备:', deviceCode);
    
    const openid = 'test_user_123456';

    wx.request({
      url: `${this.data.serverUrl}/wxapp/bind_device/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        openid: openid,
        device_code: deviceCode
      },
      success: (res) => {
        console.log('设备绑定响应:', res.data);
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '设备绑定成功', 
            icon: 'success' 
          });
          
          // 更新页面数据
          this.setData({
            deviceCode: deviceCode
          });
        } else {
          wx.showToast({ 
            title: res.data.error || '绑定失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('设备绑定失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 发送数据1
  sendData1() {
    console.log('发送数据1...');
    
    wx.request({
      url: `${this.data.serverUrl}/wxapp/send_data1/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        type: 1,
        content: '这是数据1'
      },
      success: (res) => {
        console.log('数据1发送响应:', res.data);
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '数据1发送成功', 
            icon: 'success' 
          });
        } else {
          wx.showToast({ 
            title: res.data.error || '发送失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('数据1发送失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 发送数据2
  sendData2() {
    console.log('发送数据2...');
    
    wx.request({
      url: `${this.data.serverUrl}/wxapp/send_data2/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        type: 2,
        content: '这是数据2'
      },
      success: (res) => {
        console.log('数据2发送响应:', res.data);
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '数据2发送成功', 
            icon: 'success' 
          });
        } else {
          wx.showToast({ 
            title: res.data.error || '发送失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('数据2发送失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 发送数据3
  sendData3() {
    console.log('发送数据3...');
    
    wx.request({
      url: `${this.data.serverUrl}/wxapp/send_data3/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        type: 3,
        content: '这是数据3'
      },
      success: (res) => {
        console.log('数据3发送响应:', res.data);
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '数据3发送成功', 
            icon: 'success' 
          });
        } else {
          wx.showToast({ 
            title: res.data.error || '发送失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('数据3发送失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 获取分析结果
  getAnalysis() {
    console.log('获取分析结果...');
    
    const sessionId = this.data.sessionId || wx.getStorageSync('session_id');
    
    if (!sessionId) {
      wx.showToast({ 
        title: '没有会话ID', 
        icon: 'none' 
      });
      return;
    }

    wx.request({
      url: `${this.data.serverUrl}/wxapp/get_analysis/`,
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        session_id: sessionId
      },
      success: (res) => {
        console.log('分析结果响应:', res.data);
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '分析结果获取成功', 
            icon: 'success' 
          });
          
          // 可以在这里处理分析结果数据
          console.log('分析结果:', res.data);
        } else {
          wx.showToast({ 
            title: res.data.error || '获取失败', 
            icon: 'error' 
          });
        }
      },
      fail: (err) => {
        console.error('获取分析结果失败:', err);
        wx.showToast({ 
          title: '网络错误，请重试', 
          icon: 'error' 
        });
      }
    });
  },

  // 清除会话数据
  clearSession() {
    console.log('清除会话数据...');
    
    wx.removeStorageSync('session_id');
    this.setData({
      sessionId: '',
      isCollecting: false
    });
    
    wx.showToast({ 
      title: '会话数据已清除', 
      icon: 'success' 
    });
  },

  // 显示当前状态
  showStatus() {
    const status = {
      deviceCode: this.data.deviceCode,
      sessionId: this.data.sessionId || '无',
      isCollecting: this.data.isCollecting ? '是' : '否',
      serverUrl: this.data.serverUrl
    };
    
    console.log('当前状态:', status);
    
    wx.showModal({
      title: '当前状态',
      content: `设备码: ${status.deviceCode}\n会话ID: ${status.sessionId}\n正在采集: ${status.isCollecting}\n服务器: ${status.serverUrl}`,
      showCancel: false
    });
  }
}); 