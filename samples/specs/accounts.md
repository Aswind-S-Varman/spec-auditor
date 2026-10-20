# Account Specification

## 1. Registration

A user creates an account with an email address and password.

| Field    | Type   | Length | Mandatory |
|----------|--------|--------|-----------|
| email    | string | 10     | Yes       |
| password | string | 72     | Yes       |
| phone    | string | 15     | Yes       |

Email must be in the format name@domain.tld.

## 2. Profile

The customer may update their profile at any time. Phone number is optional and
may be left blank.

## 3. Password Rules

Passwords must be at least 8 characters.

## 4. Account Deletion

A user may request account deletion. The account is marked inactive.


