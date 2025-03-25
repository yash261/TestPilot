Feature: Signup Functionality


  Scenario: Successful signup with valid credentials
    Given I am on the signup page at http://localhost:3000/signup
    And I enter 'new_user' into the username field
    And I enter 'password' into the password field
    When I click the 'Sign Up' button
    Then I should be redirected to the dashboard page at http://localhost:3000/dashboard
