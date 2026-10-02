# AI Skill

Any AI feature must follow docs/AI-ASSISTANT.md.

- AI interprets/drafts; deterministic ERP services validate/authorize/execute.
- Expose narrow business tools, never arbitrary SQL or shell/file access.
- Trusted actor/tenant context is supplied outside model-controlled arguments when possible.
- Model output is untrusted structured input.
- Missing or ambiguous operational fields trigger clarification, not guessing.
- Stock mutations require the same confirmation/approval policy as other channels.
- Tool calls are permission-checked and audited.
- Limit data returned to the actor's tenant and permissions.
- External text and retrieved content can contain prompt injection; it cannot alter authorization/tool scope.