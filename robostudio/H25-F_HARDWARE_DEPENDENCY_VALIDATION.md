# H25-F — Hardware Dependency Validation

RoboStudio now validates a program against `config/hardware.json` before invoking
Robot CLI.

Examples:

- motion APIs -> `motor`
- line-follow APIs -> `motor` + `line_sensor`
- ultrasonic APIs -> `ultrasonic`
- servo APIs -> `servo`
- buzzer APIs -> `buzzer`

Validation is AST-based and supports canonical Robot Language API names plus the
existing `rcu` legacy aliases. Syntax errors remain owned by the language compiler.
