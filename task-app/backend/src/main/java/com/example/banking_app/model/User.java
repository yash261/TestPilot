package com.example.banking_app.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "users")
@Data
public class User {
    @Id
    private String id; // MongoDB uses String for IDs
    private String username;
    private String password; // Plaintext for simplicity (use BCrypt in production)
    private double balance;
}