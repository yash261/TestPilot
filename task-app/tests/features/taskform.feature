Feature: Task Management

  Scenario: Add a new task
    Given I am on the add task page "/add"
    When I fill in the task title with "Grocery Shopping"
    And I fill in the task description with "Buy milk, eggs, and bread"
    And I click the submit button with data-testid "submit-task"
    Then I should be redirected to the tasks page "/tasks"