Feature: Login Functionality


  Scenario: Unsuccessful login with empty username
    Given I am on the login page at http://localhost:3000/
    And I enter '' into the username field
    And I enter 'password' into the password field
    When I click the 'Login' button
    Then I should see an error message indicating invalid credentials