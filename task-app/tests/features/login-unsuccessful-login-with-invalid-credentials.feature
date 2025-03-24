Feature: Login Functionality


  Scenario: Unsuccessful login with invalid credentials
    Given I am on the login page at http://localhost:3000/
    And I enter 'invalid_user' into the username field
    And I enter 'invalid_password' into the password field
    When I click the 'Login' button
    Then I should see an error message indicating invalid credentials
