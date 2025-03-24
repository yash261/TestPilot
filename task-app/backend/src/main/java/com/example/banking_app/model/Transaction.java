package com.example.banking_app.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document(collection = "transactions")
@Data
public class Transaction {
    @Id
    private String id;
    private String fromUserId;
    private String toUserId;
    private double amount;
}