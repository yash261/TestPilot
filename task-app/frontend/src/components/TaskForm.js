import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const TaskForm = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const newTask = { title, description, completed: false };
    axios.post('http://localhost:8080/api/tasks', newTask)
      .then(() => {
        setTitle('');
        setDescription('');
        navigate('/tasks');
      })
      .catch(error => console.error('Error creating task:', error));
  };

  return (
    <div className="task-form">
      <h2>Add Task</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Title:</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            data-testid="task-title"
          />
        </div>
        <div className="form-group">
          <label>Description:</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            data-testid="task-desc"
          />
        </div>
        <button type="submit" data-testid="submit-task">Add Task</button>
      </form>
    </div>
  );
};

export default TaskForm;