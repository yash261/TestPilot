Feature: Signup


  Scenario: Successful signup with valid credentials after minor design changes
    Given I am on the signup page at http://localhost:3000/signup
    And I enter "user" into the username field
    And I enter "pass" into the password field
    When I click the "Sign Up" button
    Then I am redirected to the dashboard page at http://localhost:3000/dashboard
