Feature: Dashboard


  Scenario: Successful money transfer
    Given I am on the login page at http://localhost:3000/
    And I enter 'user' into the username field
    And I enter 'pass' into the password field
    And I click the 'Login' button
    And I am on the Dashboard page at http://localhost:3000/dashboard
    When I select a user from the user dropdown
    And I enter '10' into the amount field
    And I click the 'Transfer' button
    Then I should see a success message indicating the transfer was successful
