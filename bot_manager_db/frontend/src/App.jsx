import { useState, useEffect } from 'react';
import axios from 'axios';

// Cấu hình URL của FastAPI Backend
const API_URL = 'http://localhost:8000';

function App() {
  const [bots, setBots] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    bot_type: 'combo',
    user_token: '',
    groq_key: '',
    channel_id: '',
    guild_id: '',
    rss_urls: 'https://vnexpress.net/rss/tin-moi-nhat.rss',
    dataset_path: 'data.txt',
    allowed_guilds: '',
    allowed_channels: '',
    keywords: ''
  });

  // Tải danh sách bot mỗi khi mở trang
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

  // Nút: Gửi dữ liệu xuống Backend để tạo Bot và sinh file .py
  const handleCreateBot = async (e) => {
    e.preventDefault();

    // Chuẩn hóa dữ liệu: Biến chuỗi text thành List/Int để khớp với Pydantic Backend
    const payload = {
      ...formData,
      channel_id: parseInt(formData.channel_id) || 0,
      guild_id: parseInt(formData.guild_id) || 0,
      rss_urls: formData.rss_urls.split(',').map(s => s.trim()).filter(s => s !== ""),
      keywords: formData.keywords.split(',').map(s => s.trim()).filter(s => s !== ""),
      allowed_guilds: formData.allowed_guilds.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n)),
      allowed_channels: formData.allowed_channels.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n)),
    };

    try {
      await axios.post(`${API_URL}/bots`, payload);
      alert('🚀 Thành công: Đã lưu cấu hình và sinh file code runner!');
      fetchBots(); // Cập nhật lại danh sách bên dưới
    } catch (error) {
      console.error("Lỗi POST:", error);
      alert('❌ Thất bại: Kiểm tra lại kết nối Backend hoặc Supabase.');
    }
  };

  const handleStart = async (id) => {
    try {
      await axios.post(`${API_URL}/start/${id}`);
      fetchBots();
    } catch (error) {
      alert('Không thể khởi động bot. Kiểm tra PID hoặc file code.');
    }
  };

  const handleStop = async (id) => {
    try {
      await axios.post(`${API_URL}/stop/${id}`);
      fetchBots();
    } catch (error) {
      alert('Không thể dừng bot.');
    }
  };

  return (
    <div style={{ padding: '30px', fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif', backgroundColor: '#f4f7f6', minHeight: '100vh' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50' }}>🤖 Discord Bot Manager Project</h1>

      {/* --- FORM CẤU HÌNH BOT --- */}
      <div style={{ backgroundColor: '#fff', padding: '25px', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)', marginBottom: '30px' }}>
        <h2 style={{ borderBottom: '2px solid #3498db', paddingBottom: '10px' }}>Tạo Cấu Hình Bot Mới</h2>
        <form onSubmit={handleCreateBot} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
          
          {/* Cột trái */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label><b>Tên Bot:</b></label>
            <input name="name" placeholder="VD: Bot Tin Tức 01" onChange={handleInputChange} required style={inputStyle} />

            <label><b>Loại Bot:</b></label>
            <select name="bot_type" onChange={handleInputChange} style={inputStyle}>
              <option value="combo">Combo (News + Reply)</option>
              <option value="news_agent">News Agent Only</option>
              <option value="reply_bot">Reply Bot Only</option>
            </select>

            <label><b>Discord Token:</b></label>
            <input name="user_token" type="password" placeholder="Mã token người dùng..." onChange={handleInputChange} required style={inputStyle} />

            <label><b>Groq API Key:</b></label>
            <input name="groq_key" type="password" placeholder="gsk_..." onChange={handleInputChange} required style={inputStyle} />
            
            <label><b>Keywords (cách nhau bằng dấu phẩy):</b></label>
            <input name="keywords" placeholder="AI, Crypto, Game..." onChange={handleInputChange} style={inputStyle} />
          </div>

          {/* Cột phải */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <label><b>Channel ID:</b></label>
            <input name="channel_id" placeholder="ID kênh để gửi tin" onChange={handleInputChange} style={inputStyle} />

            <label><b>Guild ID (Server):</b></label>
            <input name="guild_id" placeholder="ID Server chính" onChange={handleInputChange} style={inputStyle} />

            <label><b>RSS URLs (cách nhau bằng dấu phẩy):</b></label>
            <input name="rss_urls" defaultValue={formData.rss_urls} onChange={handleInputChange} style={inputStyle} />

            <label><b>Allowed Guilds/Channels (ID):</b></label>
            <input name="allowed_guilds" placeholder="ID Server cho Reply Bot..." onChange={handleInputChange} style={inputStyle} />

            <button type="submit" style={{ marginTop: '25px', padding: '12px', cursor: 'pointer', backgroundColor: '#3498db', color: 'white', border: 'none', borderRadius: '5px', fontWeight: 'bold' }}>
              GENERATE & SAVE BOT
            </button>
          </div>
        </form>
      </div>

      {/* --- DANH SÁCH BOT --- */}
      <div style={{ backgroundColor: '#fff', padding: '25px', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        <h2 style={{ borderBottom: '2px solid #2ecc71', paddingBottom: '10px' }}>Bot Control Panel</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '15px' }}>
          <thead>
            <tr style={{ backgroundColor: '#ecf0f1', textAlign: 'left' }}>
              <th style={tableHeaderStyle}>Tên Bot</th>
              <th style={tableHeaderStyle}>Loại</th>
              <th style={tableHeaderStyle}>Trạng thái</th>
              <th style={tableHeaderStyle}>PID</th>
              <th style={tableHeaderStyle}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {bots.map((bot) => (
              <tr key={bot.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={tableCellStyle}>{bot.name}</td>
                <td style={tableCellStyle}><code style={{backgroundColor:'#f0f0f0'}}>{bot.bot_type}</code></td>
                <td style={tableCellStyle}>
                  <b style={{ color: bot.status === 'running' ? '#2ecc71' : '#e74c3c' }}>{bot.status.toUpperCase()}</b>
                </td>
                <td style={tableCellStyle}>{bot.pid || '-'}</td>
                <td style={tableCellStyle}>
                  {bot.status === 'stopped' ? (
                    <button onClick={() => handleStart(bot.id)} style={btnStartStyle}>▶ Start</button>
                  ) : (
                    <button onClick={() => handleStop(bot.id)} style={btnStopStyle}>⏹ Stop</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Inline Styles
const inputStyle = { padding: '8px', borderRadius: '4px', border: '1px solid #ddd', marginBottom: '5px' };
const tableHeaderStyle = { padding: '12px', borderBottom: '2px solid #ddd' };
const tableCellStyle = { padding: '12px' };
const btnStartStyle = { backgroundColor: '#2ecc71', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '4px', cursor: 'pointer', marginRight: '5px' };
const btnStopStyle = { backgroundColor: '#e74c3c', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '4px', cursor: 'pointer' };

export default App;