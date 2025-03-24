Feature: Task List

  Scenario: Viewing the list of tasks
    Given the user is logged in
    When the user navigates to the "/tasks" route
    Then the user should see a list of tasks displayed in the task list

  Scenario: Marking a task as complete
    Given the user is logged in
    And the user is on the "/tasks" route
    When the user clicks the checkbox for a specific task with data-testid "task-complete"
    Then the task should be marked as complete in the list