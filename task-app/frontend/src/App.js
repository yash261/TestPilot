import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import TaskList from './components/TaskList';
import TaskForm from './components/TaskForm';
import DeleteTasks from './components/DeleteTasks';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header>
          <h1>Task Management App</h1>
          <nav>
            <Link to="/tasks" className="nav-link">Task List</Link>
            <Link to="/add-task" className="nav-link">Add Task</Link>
            <Link to="/delete-tasks" className="nav-link">Delete Tasks</Link>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/tasks" element={<TaskList />} />
            <Route path="/add-task" element={<TaskForm />} />
            <Route path="/delete-tasks" element={<DeleteTasks />} />
            <Route path="/" element={<TaskList />} /> {/* Default route */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;