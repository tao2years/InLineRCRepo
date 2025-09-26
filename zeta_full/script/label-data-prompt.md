Your job is to help me label my training data.

I have many different Markdown files that contain training that I use to
fine-tune an LLM.

The LLM is trained to complete code. It should look at a
user's recent edits, optionally the outline of the current file, the snippet
user is looking at and reply with a completion for the cursor.

I want to label that data with a limited number of labels so I
get an overview of data distribution, i.e. see how many training examples of a
certain type I have.

The training examples are all made up of XML tags for different pieces of data:

- `<events>` contains edits the user made before requesting a code completion.
- `<feedback>` and `<rating>` are comments/rating by users that submitted this example.
- `<input>` is the user's original code snippet.
- `<output>` is the code completion that we *want* the LLM to produce and which we train it on.

Example: if the user edited two files (events show up in `<events>`) and the got a completion that deleted too much code, the `<rating>` and `<feedback>` tags will contain negative feedback and the `<output>` tag will contain the correct code completion.

## Labels

Here is the list of labels I came up with:

Category 1:
- `no-op`: The input and output are identical.
- `local-edit`: LLM suggests an edit that's right next to the cursor location in the `<input>`, right where `<|user_cursor_is_here|>` shows up.
- `non-local-edit`: LLM suggests an edit that's not next to the cursor location. For example, a few lines down or up from the cursor.

If the `<output>` contains a local edit AND a non-local edit, it should be labelled `non-local-edit`.

Category 2:
- `add-imports`: User references symbols that haven't been imported yet and the LLM suggests adding them.
- `complete-implementation`: User starts typing a new function/class/... and the LLM completes the implementation.
- `complete-pattern`: User starts adding print statements, for example, LLM realises user is debugging and suggests adding more statements. Or: user adds `pub` to a struct field and LLM suggests adding it to more.
- `infer-intent`: User adds a new function in one file, starts typing the name of function in another file, and LLM suggests completing the call. Or: user deletes a struct field, LLM suggests removing it from the constructor and removing the getter function.
- `infer-refactor`: User starts typing name of a new variable, LLM realises user wants to bind local value to a variable and extracts the value to the binding.
- `unknown`: none of the labels above apply, or if they do, they apply only partially.

## Task

Here is the training data I want you to label:

```<training-data-filename>
<training-data-content>
```

Pick at least one label from each category. You should end up with at least 2 labels in total.

You MUST NOT choose than one label from a single category. Bad: `no-op,local-edit`, Good: `no-op,unknown`.

First reply with your reasoning for picking the two or more labels, then end with a separate, single line that only contains the comma-separated labels. Nothing else. The last line **must** be the comma-separated labels.
