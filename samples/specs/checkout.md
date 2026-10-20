# Checkout Specification

## 1. Overview

This document describes the checkout journey for the online store. The shopper
reviews their basket, enters delivery details, selects a payment method, and
confirms the order.

## 2. Basket Review

The customer may adjust item quantities before proceeding.

- Quantity must be greater than 0 and less than 1 for digital gift cards.
- Removing the final item returns the user to the catalogue.
- The basket total must refresh immediately after any change.

## 3. Delivery Details

The shopper enters a delivery address. Address line 1 is mandatory.
Postcode is validated against the carrier service described in section 4.2.

The system must respond quickly when validating the postcode.

## 4. Payment

The customer selects a payment method and confirms the order. On success the
order is created and a confirmation email is sent.

Orders over RM100 qualify for free shipping.

## 5. Confirmation

The confirmation screen displays the order number, delivery estimate, and total
paid. The user may return to the catalogue from this screen.


