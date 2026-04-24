// File: src/App.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

// Đặt base URL chỉ thẳng vào FastAPI Backend
const API_URL = 'http://localhost:8000';

function App() {
  const [bots, setBots] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    bot_type: 'news_agent',
    discord_token: '',
    groq_key: '',
  });

  // Load danh sách bot khi vừa mở trang
  useEffect(() => {
    fetchBots();
  }, []);

  const fetchBots = async () => {
    try {
      const res = await axios.get(`${API_URL}/bots`);
      setBots(res.data.data);
    } catch (error) {
      console.error("Lỗi khi tải danh sách bot:", error);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Nút: Tạo Bot
  const handleCreateBot = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/bots`, {
        ...formData,
        target_channel: 0, // Giá trị mặc định tạm thời
        keywords: []       // Giá trị mặc định tạm thời
      });
      alert('Tạo và sinh code Bot thành công!');
      fetchBots(); // Refresh lại list
    } catch (error) {
      console.error(error);
      alert('Lỗi khi tạo bot!');
    }
  };

  // Nút: Chạy Bot
  const handleStart = async (id) => {
    try {
      await axios.post(`${API_URL}/start/${id}`);
      fetchBots();
    } catch (error) {
      alert('Lỗi khi khởi động bot!');
    }
  };

  // Nút: Dừng Bot
  const handleStop = async (id) => {
    try {
      await axios.post(`${API_URL}/stop/${id}`);
      fetchBots();
    } catch (error) {
      alert('Lỗi khi dừng bot!');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>🤖 Bot Manager Dashboard</h1>

      {/* --- FORM TẠO BOT --- */}
      <div style={{ border: '1px solid #ccc', padding: '20px', marginBottom: '20px' }}>
        <h2>Tạo Bot Mới</h2>
        <form onSubmit={handleCreateBot} style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '400px' }}>
          <input name="name" placeholder="Tên Bot (VD: Bot Thời Sự)" onChange={handleInputChange} required />
          <select name="bot_type" onChange={handleInputChange}>
            <option value="news_agent">News Agent</option>
            <option value="reply_bot">Reply Bot</option>
            <option value="combo">Chạy cả 2 (Combo)</option>
          </select>
          <input name="discord_token" placeholder="Discord Token" onChange={handleInputChange} required />
          <input name="groq_key" placeholder="Groq API Key" onChange={handleInputChange} required />
          <button type="submit">Sinh Code & Lưu Cấu Hình</button>
        </form>
      </div>

      {/* --- DANH SÁCH BOT --- */}
      <div>
        <h2>Danh Sách Bot Đang Quản Lý</h2>
        {bots.length === 0 ? <p>Chưa có bot nào. Hãy tạo mới!</p> : (
          <table border="1" cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead>
              <tr>
                <th>Tên Bot</th>
                <th>Loại</th>
                <th>Trạng thái</th>
                <th>PID</th>
                <th>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {bots.map((bot) => (
                <tr key={bot.id}>
                  <td>{bot.name}</td>
                  <td>{bot.bot_type || 'N/A'}</td>
                  <td>
                    <span style={{ color: bot.status === 'running' ? 'green' : 'red', fontWeight: 'bold' }}>
                      {bot.status.toUpperCase()}
                    </span>
                  </td>
                  <td>{bot.pid || '-'}</td>
                  <td>
                    {bot.status === 'stopped' ? (
                      <button onClick={() => handleStart(bot.id)} style={{ background: 'green', color: 'white' }}>▶ Bắt đầu</button>
                    ) : (
                      <button onClick={() => handleStop(bot.id)} style={{ background: 'red', color: 'white' }}>⏹ Dừng lại</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default App;