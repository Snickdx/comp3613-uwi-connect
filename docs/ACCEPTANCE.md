# UWI Connect — public acceptance criteria

Derived from elicitable stakeholder needs (Phase 1). Instructor private defects are **not** listed here.

## Access

1. Alumni register and must verify a **UWI institutional email** before browsing boards or being included in campaign audiences.
2. Passwords are stored hashed; login responses never include password material.
3. Unverified accounts cannot browse published boards as alumni.

## Boards

4. Alumni may submit **job** or **event** listings; submissions stay **pending** until an admin publishes (alumni cannot publish directly).
5. Pending listings are not visible on the public boards.
6. Admin can publish or reject a pending submission.
7. Publishing a listing notifies verified alumni (in-app notification and/or equivalent).

## Campaigns

8. Admin can compose an email campaign (subject + body) and send it to the verified alumni audience.
9. Campaign send must not target unverified accounts.
10. Campaign send should not create duplicate notification rows for the same recipient/event.

## Notifications

11. Listing-publish and campaign-send share one consistent notification mechanism (subjects emit; subscribers react) so adding a new channel later does not require copy-pasting fan-out logic.
