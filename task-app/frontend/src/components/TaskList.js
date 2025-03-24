import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const TaskList = () => {
  const [tasks, setTasks] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:8080/api/tasks')
      .then(response => setTasks(response.data))
      .catch(error => console.error('Error fetching tasks:', error));
  }, []);

  const toggleComplete = (task) => {
    const updatedTask = { ...task, completed: !task.completed };
    axios.put(`http://localhost:8080/api/tasks/${task.id}`, updatedTask)
      .then(response => {
        setTasks(tasks.map(t => t.id === task.id ? response.data : t));
      })
      .catch(error => console.error('Error updating task:', error));
  };

  return (
    <div className="task-list">
      <h2>Task List</h2>
      {tasks.length === 0 ? (
        <p>No tasks available.</p>
      ) : (
        <ul data-testid="task-list">
          {tasks.map(task => (
            <li key={task.id} className={task.completed ? 'completed' : ''}>
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => toggleComplete(task)}
                data-testid="task-complete"
              />
              <span>{task.title} - {task.description}</span>
            </li>
          ))}
        </ul>
      )}
      <button onClick={() => navigate('/add-task')} data-testid="add-task-btn">Add New Task</button>
    </div>
  );
};

export default TaskList;