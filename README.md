# Cool Compiler

"Cool" is probably subjective (_actually 100% subjective_). Although a bit late into taking my first compiler course, I am glad to have taken it with one of the best and a JIT pioneer, Michael Franz. His research group's recent focus has been on binary reverse engineering, decompilation, diversification, and security. Check out his website if you are a prospective PhD student and wanted to do research in those areas (his website has information on how to contact him): [https://www.michaelfranz.com/](https://www.michaelfranz.com/).

### Memorable Quotes From Lectures 

I am recalling them from memory weeks later so they might not be exact).

_"We programmers write a program like it's flat, but program itself is very dynamic with various data structures pointing to each other and keeping track of different information."_

__Commentary__: To me, this is a nice way to think about compiler. It makes compiler feels somewhat magical. The needs to transform a flat program into a dynamic representation is especially true for an optimizing compiler, where we don't want to generate code right as we see them (like a stack-based compiler). For example, by transforming the program into a tree (e.g., AST), it allows us to defer code generation (i.e., actually perform reasoning on the program before deciding what to generate). By transforming the program into SSA (_Single Static Assignment_), the use-defs become easy to identify and copy propagation is done implicitly as a gift. I also really like the idea behind the Phi functions introduced by SSA. Quick definition, a Phi function exists at a merge point (e.g., inside a basic block that has multiple incoming edges) whose arguments are all possible values the variable can have at that merge point. Phi functions actually do not exist in the original source program. They are phantom functions introduced by SSA to assist register allocation. I like the idea of introducing something non-existent to help solve something; it is a different way of thinking that is perhaps generalizable to assist solving many other CS problems.

_"Every software problem can be solved by adding another level of indirection."_

__Commentary__: I really liked this phrase because it reminded me of the "duct tape" saying from back when I was in highschool. Back then, I was in a few hands-on engineering extracurricular activities (e.g., building an robotic arm) and we would always joke that duct tape will fix all our engineering woes. Maybe it wasn't so much of a joke because it is so true. On competition day, if the robotic arm is still not working correctly because some parts are not connected properly, just apply duct tape and finger-crossed. In the software sense, the way I see it is that indirections may not feel intuitive. It may look ugly at first sight. However, of all possible solutions it is the easiest to apply. And it works! More concretely, indirections can come in many different forms: extra variables, extra fields in a struct, or extra code. In my opinion, adding indirection is never a bad idea as long as the indirection is not brittle and is _well-documented_. Although certain indirections can also increase execution time or code size, so if those factors are important then indirections should be inplemented with more thoughts. 

_"C was developed at a time before parsing theory was fully developed."_

__Commentary__: In this course, I think we only spent one lecture on parsing. In particular, we only learn about LL(1) parsing where a single token lookahead is enough to perform the parsing step. For reason to why parsing in C or C++ is way more complicated, the first page of the project documentation (2022W-CS241-Project.pdf) has a good example. Recent languages are all designed with LL(1) parsing in mind. And it makes sense: if we can make parsing easy to perform, why not? There is also this webpage on [why parsing C is a nightmare](https://people.eecs.berkeley.edu/~necula/cil/cil016.html) that I came across on Twitter recently.
