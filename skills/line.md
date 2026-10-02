# LINE Skill

- Treat LINE as an adapter/client.
- Verify webhook signature before processing.
- Deduplicate webhook deliveries.
- Map LINE identity to ERP identity/tenant through explicit secure linking.
- Convert messages/postbacks into narrow structured commands.
- Call the same application services used by Web.
- Separate read-only queries from mutations.
- Mutation flow is normalize -> confirm -> approve if required -> execute.
- Confirmation/postback tokens are actor/tenant/request-bound, expiring and single-use.
- Permission and current approval state are revalidated when action executes.
- Keep replies concise and mobile-friendly.
- Thai/English natural language is supported.
- Ambiguous operational commands ask for missing information rather than guessing.
- Never expose raw DB/internal admin tools to LINE.