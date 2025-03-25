import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || {});
  const [users, setUsers] = useState([]);
  const [toUserId, setToUserId] = useState('');
  const [amount, setAmount] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      const usersRes = await axios.get('http://192.168.0.103:8080/api/users');
      setUsers(usersRes.data.filter(u => u.id !== user.userId));
      const transRes = await axios.get(`http://192.168.0.103:8080/api/transactions/${user.userId}`);
      setTransactions(transRes.data);
    };
    fetchData();
  }, [user.userId]);

  const handleTransfer = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://192.168.0.103:8080/api/transfer', {
        fromUserId: user.userId,
        toUserId:toUserId,
        amount: Number(amount),
      });
      setMessage('Transfer successful');
      const updatedUser = { ...user, balance: user.balance - Number(amount) };
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setAmount('');
      const transRes = await axios.get(`http://192.168.0.103:8080/api/transactions/${user.userId}`);
      setTransactions(transRes.data);
    } catch (err) {
      setMessage('Transfer failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/');
  };

  return (
    <div className="mt-5">
      <h2>Welcome, {user.username}</h2>
      <p>Balance: ${user.balance.toFixed(2)}</p>
      <button id="logout-btn" className="btn btn-danger mb-3" onClick={handleLogout}>Logout</button>

      <h3>Transfer Money</h3>
      <form onSubmit={handleTransfer}>
        <div className="mb-3">
          <label htmlFor="to-user">To User</label>
          <input
            id="to-user"
            type="text"
            className="form-control"
            value={toUserId}
            onChange={(e) => {alert(e.target.value);setToUserId(e.target.value)}}
          />
        </div>
        <div className="mb-3">
          <label htmlFor="amount">Amount</label>
          <input
            id="amount"
            type="number"
            className="form-control"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>
        <button id="transfer-btn" type="submit" className="btn btn-primary">Transfer</button>
        {message && <p id="transfer-message" className={message.includes('failed') ? 'text-danger' : 'text-success'}>{message}</p>}
      </form>

      <h3 className="mt-4">Transaction History</h3>
      <ul className="list-group">
        {transactions.map(t => (
          <li key={t.id} className="list-group-item">
            {t.fromUserId === user.userId ? 'Sent' : 'Received'} ${t.amount.toFixed(2)} 
            {t.fromUserId === user.userId ? ' to ' : ' from '} 
            {users.find(u => u.id === (t.fromUserId === user.userId ? t.toUserId : t.fromUserId))?.username}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Dashboard;