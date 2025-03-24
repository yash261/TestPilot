Feature: Login Functionality


  Scenario: Successful login with valid credentials
    Given I am on the login page at http://localhost:3000/
    And I enter 'user' into the username field
    And I enter 'pass' into the password field
    When I click the 'Login' button
    Then I should be redirected to the dashboard page at http://localhost:3000/dashboard
