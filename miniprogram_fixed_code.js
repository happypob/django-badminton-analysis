// index.js - 修复版本
Page({
  // 发送数据1
  sendData1() {
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
        wx.showToast({ title: '数据1发送成功', icon: 'success' })
        console.log('数据1发送结果:', res.data)
      },
      fail: (err) => {
        wx.showToast({ title: '发送失败', icon: 'error' })
        console.error('数据1发送失败:', err)
      }
    })
  },

  // 发送数据2
  sendData2() {
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
        wx.showToast({ title: '数据2发送成功', icon: 'success' })
        console.log('数据2发送结果:', res.data)
      },
      fail: (err) => {
        wx.showToast({ title: '发送失败', icon: 'error' })
        console.error('数据2发送失败:', err)
      }
    })
  },

  // 发送数据3
  sendData3() {
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
        wx.showToast({ title: '数据3发送成功', icon: 'success' })
        console.log('数据3发送结果:', res.data)
      },
      fail: (err) => {
        wx.showToast({ title: '发送失败', icon: 'error' })
        console.error('数据3发送失败:', err)
      }
    })
  }
}) 