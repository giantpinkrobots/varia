# Contributions guide for Varia

<br>

## About AI usage

These are non-negotiable red-lines:
- **AI generated PR descriptions and comments are not allowed. You must explain your contribution with your own words.**
- **AI generated translations are not allowed. You yourself must be fluent in the language you're doing the translations for.**

<br>

I don't disallow AI assisted PRs, and things like simple bugfixes can be entirely AI generated as well. However, substantial amounts of AI-generated code without human verification will not be allowed. I don't have concrete rules when it comes to AI assisted PRs as I don't believe there is a way to implement such rules. **If you want to know about *"what % of AI-generated code in my PR is the limit"*, your PR is not acceptable.**

Overall, your usage of AI is okay if it's along these lines:
- VS Code's Copilot autofill function
- Asking AI to figure out a mistake in your code
- A bugfix consisting of a few simple lines that was written by AI
- Using AI to generate boilerplate, or using it as a simple starting point to build from

... and not so much with these:
- Entire features implemented solely by AI
- Entire blocks of AI-generated code you left as-is (like functions)
- Code you did not check and verify yourself

There aren't guidelines about disclosure. If you do disclose your AI usage, that's fantastic. But I realize there is no way to enforce it, so it's up to you.

AI tools tend to over-engineer features and fixes, needlessly overcomplicating entire codebases. On top of that, many open source projects are struggling with AI-generated code spam which makes it extremely difficult to cherry-pick worthwhile contributions. Remember that people try their best, and inconsistencies in the enforcement of AI guidelines are ultimately inevitable. *Welcome to the modern internet.*

<br>

## Code

If you want to contribute code, you mainly want the **'next'** branch for things like new features that'll land in the next major version, as that branch is for active development. For very important bug fixes however, you want the **'main'** branch, so I can release a hotfix quickly from there without having to also release all the untested new features in development. These fixes can be applied to the 'next' branch later.

<br>

## Translations

There is now a Weblate instance for Varia, kindly provided by Weblate for free (thanks Weblate! <3). As such, the hosted Weblate instance will be used for translations from now on. It makes following through with Varia's development much easier if you're a translator. There's no need to open pull requests for each time you want to push forward an addition or change.

https://hosted.weblate.org/git/varia/varia/

The Weblate instance is for the 'next' branch, which is the development branch of Varia. However, if there is a really embarassing mistake that needs immediate correction with a hotfix, you should do a pull request for the 'main' branch here. **Please don't do this for corrections or additions that aren't super important though.**

You are allowed to submit translations that aren't 100% direct equivalents of the English strings in cases where:
- a slightly different way of saying something sounds more natural
- a direct translation will be too long and would look weird in the UI
- the translated string still has the same overall meaning

For example in the Turkish language translation, instead of "Torrenting is disabled." I've written the equivalent of "Torrent support is disabled.", because the equivalent of "Torrenting" would sound really weird. Same way, writing the equivalent of "Torrent Support Disabled" on a button in the sidebar would be too long and mess with the UI, so I left out the word "Support" and just wrote "Torrent Disabled". These kinds of changes are fine, as they still ultimately have the same meaning.

**Do not make drastic changes in your translations.** If you think there is a better way of phrasing something, suggest a change in the English string first through an issue instead of just writing mistranslations. I'll leave what constitutes a "drastic" change up to you as there is no way to draw a distinct line.
