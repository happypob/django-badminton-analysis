// index.js - 改进版本
Page({
  data: {
    // 页面数据
  },

  // 发送数据1 - 改进版本
  sendData1() {
    console.log('开始发送数据1...')
    
    wx.request({
      url: 'http://192.168.125.130:9000/wxapp/send_data1/',
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        type: 1,
        content: '这是数据1'
      },
      success: (res) => {
        console.log('数据1发送成功:', res)
        console.log('响应状态码:', res.statusCode)
        console.log('响应数据:', res.data)
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '数据1发送成功', 
            icon: 'success',
            duration: 2000
          })
        } else {
          wx.showToast({ 
            title: `发送失败: ${res.statusCode}`, 
            icon: 'error',
            duration: 3000
          })
        }
      },
      fail: (err) => {
        console.error('数据1发送失败:', err)
        wx.showToast({ 
          title: '网络错误', 
          icon: 'error',
          duration: 3000
        })
      }
    })
  },

  // 发送数据2 - 改进版本
  sendData2() {
    console.log('开始发送数据2...')
    
    wx.request({
      url: 'http://192.168.125.130:9000/wxapp/send_data2/',
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        type: 2,
        content: '这是数据2'
      },
      success: (res) => {
        console.log('数据2发送成功:', res)
        console.log('响应状态码:', res.statusCode)
        console.log('响应数据:', res.data)
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '数据2发送成功', 
            icon: 'success',
            duration: 2000
          })
        } else {
          wx.showToast({ 
            title: `发送失败: ${res.statusCode}`, 
            icon: 'error',
            duration: 3000
          })
        }
      },
      fail: (err) => {
        console.error('数据2发送失败:', err)
        wx.showToast({ 
          title: '网络错误', 
          icon: 'error',
          duration: 3000
        })
      }
    })
  },

  // 发送数据3 - 改进版本
  sendData3() {
    console.log('开始发送数据3...')
    
    wx.request({
      url: 'http://192.168.125.130:9000/wxapp/send_data3/',
      method: 'POST',
      header: {
        'content-type': 'application/x-www-form-urlencoded'
      },
      data: {
        type: 3,
        content: '这是数据3'
      },
      success: (res) => {
        console.log('数据3发送成功:', res)
        console.log('响应状态码:', res.statusCode)
        console.log('响应数据:', res.data)
        
        if (res.statusCode === 200) {
          wx.showToast({ 
            title: '数据3发送成功', 
            icon: 'success',
            duration: 2000
          })
        } else {
          wx.showToast({ 
            title: `发送失败: ${res.statusCode}`, 
            icon: 'error',
            duration: 3000
          })
        }
      },
      fail: (err) => {
        console.error('数据3发送失败:', err)
        wx.showToast({ 
          title: '网络错误', 
          icon: 'error',
          duration: 3000
        })
      }
    })
  },

  // 测试所有接口
  testAllInterfaces() {
    console.log('开始测试所有接口...')
    
    // 依次测试三个接口
    setTimeout(() => this.sendData1(), 0)
    setTimeout(() => this.sendData2(), 1000)
    setTimeout(() => this.sendData3(), 2000)
  },

  // 页面加载时
  onLoad() {
    console.log('页面加载完成')
    console.log('后端服务器地址: http://192.168.125.130:9000')
  }
}) 