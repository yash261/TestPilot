Feature: Delete Tasks

  Scenario: Viewing and deleting tasks from the Delete Tasks page
    Given the user is logged in
    When the user navigates to the "/delete" route
    Then the user should see a list of tasks

  Scenario: Deleting a task successfully
    Given the user is logged in
    And the user is on the "/delete" route
    When the user clicks the delete button for a specific task with data-testid "delete-task-{task.id}"
    Then the task should be removed from the list of tasks