import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const DeleteTasks = () => {
  const [tasks, setTasks] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:8080/api/tasks')
      .then(response => setTasks(response.data))
      .catch(error => console.error('Error fetching tasks:', error));
  }, []);

  const deleteTask = (id) => {
    axios.delete(`http://localhost:8080/api/tasks/${id}`)
      .then(() => {
        setTasks(tasks.filter(task => task.id !== id));
      })
      .catch(error => console.error('Error deleting task:', error));
  };

  return (
    <div className="delete-tasks">
      <h2>Delete Tasks</h2>
      {tasks.length === 0 ? (
        <p>No tasks to delete.</p>
      ) : (
        <ul>
          {tasks.map(task => (
            <li key={task.id}>
              {task.title} - {task.description}
              <button
                onClick={() => deleteTask(task.id)}
                data-testid={`delete-task-${task.id}`}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
      <button className="back-button" onClick={() => navigate('/tasks')}>Back to Task List</button>
    </div>
  );
};

export default DeleteTasks;