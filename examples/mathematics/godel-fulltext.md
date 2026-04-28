# 0 About this document

G¨odel’s famous proof \[2, 1\] is highly interesting, but may be hard to understand. Some of this difficulty is due to the fact that the notation used by G¨odel has been largely replaced by other notation. Some of this difficulty is due to the fact that while G¨odel’s formulations are concise, they sometimes require the readers to make up their own interpretations for formulae, or to keep definitions in mind that may not seem mnemonic to them.

This document is a translation of a large part of G¨odel’s proof. The translation happens on three levels:

• from German to English

• from G¨odel’s notation to more common mathematical symbols

• from paper to hyper-text

Hyper-text and colors are used as follows: definitions take place in blue italics, like this: defined term. Wherever the defined term is used, we have a red hyper-link to the place in the text where the term was first defined, like this: defined term. Furthermore, each defined term appears in the clickable index at the end of this document. In the margin of the document, there are page-numbers like this \[173\], which refer to the original document. Here are links for looking up something by page: 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 196. Finally, small text snippets in magenta are comments not present in the original text, but perhaps useful for the reader.

This translation omits all foot-notes from the original, and only contains sections 1 and 2 (out of four).

The translation comes as-is, with no explicit or implied warranty. Use at your own risk, the translator is not willing to take any responsibility for problems you might have because of errors in the translation, or because of misunderstandings. You are permitted to reproduce this document all you like, but only if you include this notice.

# On formally undecidable propositions of Principia Mathematica and related systems I

Kurt G¨odel

1931

# 1 Introduction

The development of mathematics towards greater exactness has, as is well-known, lead to formalization of large areas of it such that you can carry out proofs by following a few mechanical rules. The most comprehensive current formal systems are the system of Principia Mathematica (PM) on the one hand, the Zermelo-Fraenkelian axiom-system of set theory on the other hand. These two systems are so far developed that you can formalize in them all proof methods that are currently in use in mathematics, i.e. you can reduce these proof methods to a few axioms and deduction rules. Therefore, the conclusion seems plausible that these deduction rules are sufficient to decide all mathematical questions expressible in those systems. We will show that this is not true, but that there are even relatively easy problem in the theory of ordinary whole numbers that can not be decided from the axioms. This is not due to the nature of these systems, but it is true for a very wide class of formal systems, which in particular includes all those that you get by adding a finite number of axioms to the above mentioned systems, provided the additional axioms don’t make false theorems provable.

Let us first sketch the main intuition for the proof, without going into detail and of course without claiming to be exact. The formulae of a formal system (we will restrict ourselves to the $P M$ here) can be viewed syntactically as finite sequences of the basic symbols (variables, logical constants, and parentheses or separators), and it is easy to define precisely which sequences of the basic symbols are syntactically correct formulae and which are not. Similarly, proofs are formally nothing else than finite sequences of formulae (with specific definable properties). Of course, it is irrelevant for meta-mathematical observations what signs are taken for basic symbols, and so we will chose natural numbers for them. Hence, a formula is a finite sequence of natural numbers, and a proof schema is a finite sequence of finite sequences of natural numbers. The meta-mathematical concepts (theorems) hereby become concepts (theorems) about natural numbers, which makes them (at least partially) expressible in the symbols of the system $\\quad .$ . In particular, one can show that the concepts “formula”, “proof schema”, “provable formula” are all expressible within the system $P M$ , i.e. one can, for example, come up with a formula $F ( v )$ of $\\cdot$ that has one free variable $v$ (whose type is sequence of numbers) such that the semantic interpretation of $F ( v )$ is: $v$ is a provable formula. We will now construct an undecidable theorem of the system $\\cdot$ , i.e. a theorem $A$ for which neither $A$ nor $\\neg A$ is provable, as follows:

We will call a formula of $\\cdot$ with exactly one free variable of type natural numbers a class-sign. We will assume the class-signs are somehow numbered, call the $n$ th one $R \_ { n }$ , and note that both the concept “class-sign” and the ordering relation $R$ are definable within the system $\\quad .$ . Let $\\alpha$ be an arbitrary class-sign; with $\\alpha ( n )$ we denote the formula that you get when you substitute $n$ for the free variable of $\\alpha$ . Also, the ternary relation $x \\Leftrightarrow y ( z )$ is definable within $\\cdot$ . Now we will define a class $K$ of natural numbers as follows:

$$
K = { n \\in \\mathbb { N } \\mid \\neg p r o v a b l e ( R \_ { n } ( n ) ) }
$$

(where $p r o v a b l e ( x )$ means $x$ is a provable formula). With other words, $\\kappa$ is the set of numbers $\\cdot$ where the formula $R \_ { n } ( n )$ that you get when you insert $\\cdot$ into its own formula $R \_ { n }$ is improvable. Since all the concepts used for this definition are themselves definable in $P M$ , so is the compound concept $K$ , i.e. there is a class-sign $S$ such that the formula $S ( n )$ states that $n \\in K$ . As a class-sign, $S$ is identical with a specific $R \_ { q }$ , i.e. we have

$$
S \\Leftrightarrow R \_ { q }
$$

for a specific natural number $q$ . We will now prove that the theorem $R \_ { q } ( q )$ is undecidable within $P M$ . We can understand this by simply plugging in the definitions: $R \_ { q } ( q ) \\Leftrightarrow S ( q ) \\Leftrightarrow q \\in K \\Leftrightarrow \\neg p r o v a b l e ( R \_ { q } ( q ) )$ , in other words, $R \_ { q } ( q )$ states “I am improvable.” Assuming the theorem $R \_ { q } ( q )$ were provable, then it would also be true, i.e. because of $( 1 ) \\neg p r o v a b l e ( R \_ { q } ( q ) )$ would be true in contradiction to the assumption. If on the other hand $\\neg R \_ { q } ( q )$ were provable, then we would have $q \\notin K$ , i.e. $p r o v a b l e ( R \_ { q } ( q ) )$ . That means that both $R \_ { q } ( q )$ and $\\neg R \_ { q } ( q )$ would be provable, which again is impossible.

The analogy of this conclusion with the Richard-antinomy leaps to the eye; there is also a close kinship with the liar-antinomy, because our undecidable theorem $R \_ { q } ( q )$ states that $q$ is in $K$ , i.e. according to (1) that $R \_ { q } ( q )$ is not provable. Hence, we have in front of us a theorem that states its own unprovability. The proof method we just applied is obviously applicable to any formal system that on the one hand is expressive enough to allow the definition of the concepts used above (in particular the concept “provable formula”), and in which on the other hand all provable formulae are also true. The following exact implementation of the proof will among other things have the goal to replace the second prerequisite by a purely formal and much weaker one.

From the remark that $R \_ { q } ( q )$ states its own improvability it immediately follows that $R \_ { q } ( q )$ is correct, since $R \_ { q } ( q )$ is in fact unprovable (because it is undecidable). The theorem which is undecidable within the system PM has hence been decided by metamathematical considerations. The exact analysis of this strange fact leads to surprising results about consistency proofs for formal systems, which will be discussed in section 4 (theorem XI).

# 2 Main Result

We will now exactly implement the proof sketched above, and will first give an exact description of the formal system $P$ , for which we want to show the existence of undecidable theorems. By and large, $P$ is the system that you get by building the logic of $P M$ on top the Peano axioms (numbers as individuals, successor-relation as undefined basic concept).

# 2.1 Definitions

The basic signs of system $P$ are the following:

I. Constant: “¬” (not), “∨” (or), $" \\forall "$ (for all), “0” (zero), “succ” (the successor of), “(”, “)” (parentheses). G¨odel’s original text uses a different notation, but the reader may be more familiar with the notation adapted in this translation.

II. Variable of type one (for individuals, i.e. natural numbers including 0): “ $x \_ { 1 } { } ^ { \\dag }$ , “y1”, “ ”, . . . Variables of type two (for classes of individuals, i.e. subsets of $\\bar { }$ ): “ $x \_ { 2 }$ ”, “y2”, “ $z \_ { 2 } ^ { \ l , \ l , \ l }$ , Variables of type three (for classes of classes of individuals, i.e. sets of subsets of IN): “ $x \_ { 3 } ^ { \\phantom { \\dagger } } { } ^ { \\gamma }$ , “y3”, “ $z \_ { 3 } ^ { \ l , \ l , \ l }$ , . And so on for every natural number as type.

Remark: Variables for binary or $n$ -ary functions (relations) are superfluous as basic signs, because one can define relations as classes of ordered pairs and ordered pairs as classes of classes, e.g. the ordered pair $( a , b )$ by ${ { a } , { a , b } }$ , where ${ x , y }$ and ${ x }$ stand for the classes whose only elements are $x , y$ and $x$ , respectively.

By a sign of type one we understand a combination of signs of the form

$$
a , s u c c ( a ) , s u c c ( s u c c ( a ) ) , s u c c ( s u c c ( s u c c ( s u c c ( a ) ) ) , \\ldots \\quad \\mathrm { e t c . } ,
$$

where $a$ is either 0 or a variable of type one. In the first case we call such a sign a number-sign. For $n > 1$ we will understand by a sign of type $n$ a variable of type $\\cdot$ . We call combinations of signs of the form $a ( b )$ , where $b$ is a sign of type $n$ and $a$ a sign of type $n + 1$ , elementary formulae. We define the class of formulae as the smallest set that contains all elementary formulae and that contains for $a , b$ always also $\\neg ( a )$ , $( a ) \\lor ( b ) , \\forall x . ( a )$ (where $x$ is an arbitrary variable). We call $( a ) \\lor ( b )$ the disjunction of $a$ and $b$ , $\\neg ( a )$ the negation and $\\forall x . ( a )$ the generalization of $a$ . A formula that contains no free variables (where free variables is interpreted in the usual manner) is called proposition-formula. We call a formula with exactly $n$ free individual-variables (and no other free variables) an $n$ -ary relation sign, for $n = 1$ also class-sign.

$\\mathrm { 3 y \ s u b s t } a \\binom { v } { b }$ (where $a$ is a formula, $\\boldsymbol { v }$ is a variable, and $b$ is a sign of the same type as $\\boldsymbol { v }$ ) we understand the formula that you get by substituting $b$ for every free occurrence of $\\boldsymbol { v }$ in $a$ . We say that a formula $a$ is a type-lift of another formula $b$ if you can obtain $a$ from $b$ by increasing the type of all variables occurring in $a$ by the same number.

The following formulae (I through V) are called axioms (they are written with the help of the abbreviations (defined in the usual manner) $\\land , \\Rightarrow$ , $\\Leftrightarrow$ , $\\exists x , =$ , and using the customary conventions for leaving out parentheses):

I. The Peano axioms, which give fundamental properties for natural numbers.

1. $\\lnot ( s u c c ( x \_ { 1 } ) = 0$ ) We start to count at 0.
2. $s u c c ( x \_ { 1 } ) = s u c c ( y \_ { 1 } ) \\Rightarrow x \_ { 1 } = y \_ { 1 }$ If two natural numbers $x \_ { 1 , 2 } \\in \\mathbb { N }$ have the same successor, they are equal.
3. $\\Bigl ( x \_ { 2 } ( 0 ) \\land \\forall x \_ { 1 } \\land x \_ { 2 } ( x \_ { 1 } ) \\Rightarrow x \_ { 2 } ( s u c c ( x \_ { 1 } ) ) \\Bigr ) \\Rightarrow \\forall x \_ { 1 } \\land x \_ { 2 } ( x \_ { 1 } )$ We can prove a predicate $x \_ { 2 }$ on natural numbers by natural induction.

II. Every formula obtained by inserting arbitrary formulae for $p , q , r$ in the following schemata. We call these proposition axioms.

1. $p \\vee p \\Rightarrow p$
2. $p \\Rightarrow p \\lor q$
3. $p \\vee q \\Rightarrow q \\vee p$
4. $( p \\Rightarrow q ) \\Rightarrow ( r \\lor p \\Rightarrow r \\lor q )$

III. Every formula obtained from the two schemata

1. $\\begin{array} { r l } { ( \\forall v \\cdot a ) \\Rightarrow \\quad } & { { } a \\binom { v } { c } } \\end{array}$
2. $( \\forall v \\boldsymbol { \\cdot } b \\lor a ) \\Rightarrow ( b \\lor \\forall v \\boldsymbol { \\cdot } a )$

by inserting the following things for $a , v , b , c$ (and executing the operation denoted by subst in 1.):

Insert an arbitrary formula for $a$ , an arbitrary variable for $\\boldsymbol { v }$ , any formula where $\\boldsymbol { v }$ does not occur free for $b$ , and for $c$ a sign of the same type as $\\boldsymbol { v }$ with the additional requirement that $c$ does not contain a free variable that would be bound in a position in $a$ where $v$ is free.

For lack of a better name, we will call these quantor axioms.

IV. Every formula obtained from the schema

$$
1 . \ \\exists u . \\forall v . ( u ( v ) \\Leftrightarrow a )
$$

by inserting for $\\boldsymbol { v }$ and $u$ any variables of type $n$ and $n + 1$ respectively and for $a$ a formula that has no free occurrence of $u$ . This axiom takes the place of the reducibility axiom (the comprehension axiom of set theory).

V. Any formula obtained from the following by type-lift (and the formula itself):

$$
\\begin{array} { r } { \ l . \ \\left( \\forall x \_ { 1 } \\cdot \\left( x \_ { 2 } ( x \_ { 1 } ) \\Leftrightarrow y \_ { 2 } ( x \_ { 1 } ) \\right) \\right) \\Rightarrow x \_ { 2 } = y \_ { 2 } } \\end{array}
$$

This axiom states that a class is completely determined by its elements. Let us call it the set axiom.

A formula $c$ is called the immediate consequence of $a$ and $b$ (of $a$ ) if $a$ is the formula $\\neg b \\lor c$ (or if $c$ is the formula $\\forall v \\cdot a$ , where $\\boldsymbol { v }$ is any variable). The class of provable formulae is defined as the smallest class of formulae that contains the axioms and is closed under the relation “immediate consequence”.

# 2.2 G¨odel-numbers

We will now uniquely associate the primitive signs of system $\\cdot$ with natural numbers as follows:

$$
\\begin{array} { c c c c } { { } } & { { ^ { \\mathrm { c c } } 0 ^ { \\mathfrak { P } } \\textrm { . . . 1 } } } & { { ^ { \\mathrm { c s } } s u c c ^ { \\mathfrak { P } } \\textrm { . . . 3 } } } & { { ^ { \\mathrm { c c } } \\mathrm { . 7 } } } \ { { } } & { { ^ { \\mathrm { c c } } \\vee { ^ { \\mathfrak { P } } } \\textrm { . . . 7 } } } & { { ^ { \\mathrm { c c } } \\forall ^ { \\mathfrak { P } } \\textrm { . . . 9 } } } & { { ^ { \\mathrm { c c } } \\mathrm { . ~ . ~ 1 1 } } } \ { { } } & { { } } & { { ^ { \\mathrm { c c } } \\mathrm { . ~ . ~ 1 3 } } } & { { ^ { \\mathrm { c c } } \\mathrm { . ~ . ~ 1 3 } } } \\end{array}
$$

Furthermore we will uniquely associate each variable of type $\\cdot$ with a number of the form $p ^ { n }$ (where $p$ is a prime $> 1 3$ ). Thus there is a one-to-one-correspondence between every finite string of basic signs and a sequence of natural numbers. We now map the sequences of natural numbers (again in one-to-one correspondence) to natural numbers by having the sequence $n \_ { 1 } , n \_ { 2 } , \\ldots , n \_ { k }$ correspond to the number $2 ^ { n \_ { 1 } } { \\cdot } 3 ^ { n \_ { 2 } } { \\cdot } . . { \\cdot } p \_ { k } ^ { n \_ { k } }$ , where $p \_ { k }$ is the $k$ th prime (by magnitude). Thus, there is not only a uniquely associated natural number for every basic sign, but also for every sequence of basic signs. We will denote the number associated with the basic sign (resp. the sequence of basic signs) $a$ by $\\Phi ( a )$ . Now let $R ( a \_ { 1 } , a \_ { 2 } , \\ldots , a \_ { n } )$ be a given class or relation between basic signs or sequences of them. We will associate that with the class (relation) $R ^ { \\prime } ( x \_ { 1 } , x \_ { 2 } , \\ldots , x \_ { n } )$ that holds between $x \_ { 1 } , x \_ { 2 } , \\ldots , x \_ { n }$ if and only if there are $a \_ { 1 } , a \_ { 2 } , \\ldots , a \_ { n }$ such that for $i = 1 , 2 , \\dots , n$ we have $x \_ { i } = \\Phi ( a \_ { i } )$ and the $R ( a \_ { 1 } , a \_ { 2 } , \\ldots , a \_ { n } )$ holds. We will denote the classes and relations on natural numbers which are associated with the meta-mathematical concepts, e.g. “variable”, “formula”, “proposition-formula”, “axiom”, “provable formula” etc., in the above mentioned manner, by the same word in small caps. The proposition that there are undecidable problems in system $\\cdot$ for example reads like this: There are proposition-formulae $a$ , such that neither $a$ nor the negation of $a$ is a provable formula.

# 2.3 Primitive recursion

At this point, we will make an excursion to make an observation that a priori does not have anything to do with the system $P$ , and will first give the following definition: we

say a number-theoretical formula $\\phi ( x \_ { 1 } , x \_ { 2 } , \\ldots , x \_ { n } )$ is defined via primitive recursion in terms of the number-theoretical formulae $\\psi ( x \_ { 1 } , x \_ { 2 } , \\dots , x \_ { n - 1 } )$ and $\\mu ( x \_ { 1 } , x \_ { 2 } , \\ldots , x \_ { n + 1 } )$ if the following holds for all $x \_ { 2 } , \\ldots , x \_ { n } , k$ :

$$
\\begin{array} { c } { \\phi ( 0 , x \_ { 2 } , \\ldots , x \_ { n } ) = \\psi ( x \_ { 2 } , \\ldots , x \_ { n } ) , } \ { \\phi ( k + 1 , x \_ { 2 } , \\ldots , x \_ { n } ) = \\mu ( k , \\phi ( k , x \_ { 2 } , \\ldots , x \_ { n } ) , x \_ { 2 } , \\ldots , x \_ { n } ) } \\end{array}
$$

We call a number-theoretical formula $\\phi$ primitive recursive if there is a finite sequence of number-theoretical formulae $\\phi \_ { 1 } , \\phi \_ { 2 } , \\ldots , \\phi \_ { n }$ ending in $\\phi$ such that every function $\\phi \_ { k }$ of the sequence is either defined from two of the preceding formulae by primitive recursion or results by inserting into any of the preceding ones or, and this is the base case, is a constant or the successor function $s u c c ( x ) = x + 1$ . The length of the shortest sequence of $\\phi \_ { i }$ belonging to a primitive recursive function $\\phi$ is called its degree. We call a relation $R ( x \_ { 1 } , \\ldots , x \_ { n } )$ primitive recursive if there is a primitive recursive function $\\phi ( x \_ { 1 } , \\ldots , x \_ { n } )$ such that for all $x \_ { 1 } , x \_ { 2 } , \\ldots , x \_ { n }$ ,

$$
R ( x \_ { 1 } , \\ldots , x \_ { n } ) \\Leftrightarrow ( \\phi ( x \_ { 1 } , \\ldots , x \_ { n } ) = 0 ) .
$$

The following theorems hold:

I. Every function (relation) that you get by inserting primitive recursive functions in the places of variables of other primitive recursive functions (relations) is itself primitive recursive; likewise every function that you get from primitive recursive functions by the schema (2).

II. If $R$ and $S$ are primitive recursive relations, then so are $\\neg R , R \\lor S$ (and therefore also $R \\wedge S$ ).

III. If the functions $\\phi ( \\vec { x } ) , \\psi ( \\vec { y } )$ are primitive recursive, then so is the relation $\\phi ( \\vec { x } ) =$ $\\psi ( \\vec { y } )$ . We have resorted to a vector notation $\\bar { x }$ to denote finite-length tuples of variables.

IV. If the function $\\phi ( \\vec { x } )$ and the relation $R ( y , { \\vec { z } } )$ are primitive recursive, then so are the relations $S , T$

$$
S ( \\vec { x } , \\vec { z } ) \\Leftrightarrow \\big ( \\exists y \\leq \\phi ( \\vec { x } ) . R ( y , \\vec { z } ) \\big )
$$

$$
T ( \\vec { x } , \\vec { z } ) \\Leftrightarrow \\big ( \\forall y \\leq \\phi ( \\vec { x } ) . R ( y , \\vec { z } ) \\big )
$$

as well as the function $\\psi$

$$
\\psi ( { \\vec { x } } , { \\vec { z } } ) = \\left( \\mathbf { a r g m i n } y \\leq \\phi ( { \\vec { x } } ) \\cdot R ( y , { \\vec { z } } ) \\right)
$$

where argmin $x \\leq f ( x ) . F ( x )$ stands for the smallest $x$ for which $x \\leq f ( x ) ) \\land$ $F ( x )$ holds, and for 0 if there is no such number. Readers to whom an operational description appeals more may want to think of this as a loop that tries every value from $\\mathit { 1 }$ to $\\phi ( \\vec { x } )$ to determine the result. The crucial point here is this theorem does not state that an unbounded loop (or recursion) is primitive recursive; those are in fact strictly more powerful in terms of computability.

Theorem I follows immediately from the definition of “primitive recursive”. Theorems II and III are based upon the fact that the number-theoretical functions

$$
\\alpha ( x ) , \\beta ( x , y ) , \\gamma ( x , y )
$$

corresponding to the logical concepts $\\neg , \\lor , =$ (where $n = 0$ is taken for true and $n \\neq 0$ for false), namely

$$
{ \\begin{array} { r l } & { \\alpha ( x ) = \\left{ { \\begin{array} { l l } { 1 } & { { \\mathrm { f o r ~ } } x = 0 } \ { 0 } & { { \\mathrm { f o r ~ } } x \\neq 0 } \\end{array} } \\right. } \ & { \\beta ( x , y ) = \\left{ { \\begin{array} { l l } { 0 } & { { \\mathrm { i f ~ o n e ~ o r ~ b o t h ~ o f ~ } } x , y { \\mathrm { ~ a r e ~ } } = 0 } \ { 1 } & { { \\mathrm { i f ~ b o t h ~ } } x , y { \\mathrm { ~ a r e ~ } } \\neq 0 } \\end{array} } \\right. } \ & { \\gamma ( x , y ) = \\left{ { \\begin{array} { l l } { 0 } & { { \\mathrm { i f ~ } } x = y } \ { 1 } & { { \\mathrm { i f ~ } } x \\neq y } \\end{array} } \\right. } \\end{array} }
$$

are primitive recursive, as one can easily convince oneself. The proof for theorem IV is, in short, the following: by assumption there is a primitive recursive $\\rho ( y , \\vec { z } )$ such that:

$$
R ( y , \\vec { z } ) \\Leftrightarrow ( \\rho ( y , \\vec { z } ) = 0 )
$$

Using the recursion-schema (2) we now define a function $\\chi ( y , \\vec { z } )$ as follows:

$$
\\begin{array} { c } { { \\chi ( 0 , \\vec { z } ) = 0 } } \ { { \\chi ( n + 1 , \\vec { z } ) = ( n + 1 ) \\cdot A + \\chi ( n , \\vec { z } ) \\cdot ( A ) } } \\end{array}
$$

where $\\begin{array} { r l } { A = } & { { } \\left( \\begin{array} { l } { \\left( \\rho ( 0 , \\vec { z } ) \\right) } \\end{array} \\right) \\cdot \\begin{array} { l r } { \\left( \\rho ( n + 1 , \\vec { z } ) \\right) \\cdot } & { \\left( \\chi ( n , \\vec { z } ) \\right) } \\end{array} } \\end{array}$ .

$A$ , which makes use of the above defined $\\alpha$ and of the fact that a product is $0$ if one of its factors is $^ { - 0 }$ , can be described by the following pseudo-code:

$A = \\mathbf { i f } ( \\rho ( 0 , \\vec { z } ) = 0 )$ then 0 else $\\mathbb { f } ( \\rho ( n + 1 , \\vec { z } ) \\neq 0 )$ ) then 0 else if(χ(n, ~z) 6= 0) then 0 else 1

It is a nice example for how arithmetic can be used to emulate logics.

Therefore, $\\chi ( n + 1 , \\vec { z } )$ is ${ \\mathrm { e i t h e r } } = n + 1$ (if $A = 1$ ) $\\mathrm { o r } = \\chi ( n , { \\vec { z } } )$ (if $A = 0$ ). Obviously, the first case will occur if and only if all factors of $A$ are $1$ , i.e. if we have

$$
\\neg R ( 0 , \\vec { z } ) \\wedge R ( n + 1 , \\vec { z } ) \\wedge ( \\chi ( n , \\vec { z } ) = 0 ) .
$$

This implies that the function $\\chi ( n , \\vec { z } )$ (viewed as a function of $n$ ) remains 0 up to the smallest value of $n$ for which $R ( n , { \\vec { z } } )$ holds, and has that value from then on (if $R ( 0 , \\vec { z } )$ already holds then $\\chi ( n , \\vec { z } )$ is correspondingly constant $\\mathrm { { a n d } = 0 }$ ). Therefore, we have

$$
\\begin{array} { l } { { \\psi ( \\vec { x } , \\vec { z } ) = \\chi ( \\phi ( \\vec { x } ) , \\vec { z } ) } } \ { { S ( \\vec { x } , \\vec { z } ) \\Leftrightarrow R ( \\psi ( \\vec { x } , \\vec { z } ) , \\vec { z } ) . } } \\end{array}
$$

It is easy to reduce the relation $T$ to a case analogous to that of $S$ by negation. This concludes the proof of theorem IV.

# 2.4 Expressing metamathematical concepts

As one can easily convince oneself, the functions $x + y$ , $x \\cdot y$ , $x ^ { y }$ and furthermore the relations $x \ < y$ and $x = y$ are primitive recursive. For example, the function $x + y$ can be constructed as $0 + y = y$ and $( k + 1 ) + y = s u c c ( k + y )$ , i.e. $\\psi ( y ) = y$ and $\\mu ( k , l , y ) =$ $s u c c ( l )$ in schema (2). Using these concepts, we will now define a sequence of functions (relations) 1-45, each of which is defined from the preceding ones by the methods given by theorems I through IV. In doing so, usually multiple of the definition steps allowed by theorems I through IV are combined in one. Each of the functions (relations) 1-45, among which we find for example the concepts “formula”, “axiom”, and “immediate consequence”, is therefore primitive recursive.

1. $y \\mid x \\Leftrightarrow \\exists z \\leq x . x = y \\cdot z$

   $x$ is divisible by $y$ . 2. $i s P r i m e ( x ) \\Leftrightarrow \\neg { \\left( \\exists z \\leq x . ( z \\neq 1 \\land z \\neq x \\land z \| x ) \\right) } \\land \\left( x > 1 \\right)$

   $x$ is a prime number.

2. prFactor $\\cdot ( 0 , x ) = 0$ $\\begin{array} { r l r } { p r F a c t o r ( n + 1 , x ) = } & { { } \\quad } & { y \\leq x . \\left( i s P r i m e ( y ) \\wedge y \\mid x \\wedge y > p r F a c t o r ( n , x ) \\right) } \\end{array}$ prFactor $( n , x )$ is the $n$ th (by size) prime number contained in $x$ .

3. 0! = 1


$$
\\begin{array} { r l r l } & { \\mathrm { ~ \ - ~ } ^ { \\bot } } \ & { \\mathrm { ~ \ + \_ { \\rho } 1 ) ! = ( n + 1 ) \\cdot n ! ~ } } & & { } \ & { \\hbar P r i m e { ( 0 ) } = 0 } \ & { \\hbar P r i m e { ( n + 1 ) } = } & & { \\mathrm { \ ~ } y \\leq ( n t h P r i m e ( n ) ! + 1 ) \\cdot \\left( i s P r i m e ( y ) \\wedge y > n t h P r i m e ( n ) \\right) } \\end{array}
$$

nt  nthPrime $( n )$ is the $n$ th (by size) prime number.

6. $i t e m ( n , x ) = \\operatorname { a r g m i n } y \\leq x . \\left( ( p r F a c t o r ( n , x ) ^ { y } \\mid x ) \\land \\lnot ( p r F a c t o r ( n , x ) ^ { y + 1 } \\mid x ) \\right)$ $i t e m ( n , x )$ is the $n$ th item of the sequence of numbers associated with $x$ (for $n > 0$ and $n$ not larger than the length of this sequence).

7. $l e n g t h ( x ) = \\operatorname { a r g m i n } y \\leq x . \\left( p r F a c t o r ( y , x ) > 0 \\land p r F a c t o r ( y + 1 , x ) = 0 \\right)$

   length $\\iota ( x )$ is the length of the sequence of numbers associated with $x$ .

8. $x \\circ y = \\qquad z \\leq n t h P r i m e ( l e n g t h ( x ) + l e n g t h ( y ) ) ^ { x + y } .$ . $( \\forall n \\leq l e n g t h ( x ) . i t e m ( n , z ) = i t e m ( n , x ) ) \\land$ $( \\forall 0 < n \\leq l e n g t h ( y ) . i t e m ( n + l e n g t h ( x ) , z ) = i t e m ( n , y ) )$


$x \\textdegree y$ corresponds to the operation of “concatenating” two finite sequences of numbers.

9. $s e q ( x ) = 2 ^ { x }$

   $s e q ( x )$ corresponds to the number sequence that consists only of the number $x$ (for $x > 0$ ).

10. $p a r e n ( x ) = s e q ( 1 1 ) \\circ x \\circ s e q ( 1 3 )$

   $p a r e n ( x )$ corresponds to the operation of “parenthesizing” (11 and 13 are associated with the primitive signs “(” and “)”). 11. $v t y p e ( n , x ) \\Leftrightarrow \\left( \\exists 1 3 < z \\leq x . i s P r i m e ( z ) \\land x = z ^ { n } \\right) \\land n \\neq 0$

   $x$ is a variable of type $n$ .

11. is $V a r ( x ) \\Leftrightarrow \\exists n \\leq x . v t y p e ( n , x )$ $x$ is a variable.

12. $n o t ( x ) = s e q ( 5 ) \\circ p a r e n ( x )$

   $n o t ( x )$ is the negation of $x$ . 14. $o r ( x , y ) = p a r e n ( x ) \\circ s e q ( 7 ) \\circ p a r e n ( y )$

   $o r ( x , y )$ is the disjunction of $x$ and $y$ .

   1 $\\breve { \\mathrm { . } } \ f o r a l l ( x , y ) = s e q ( 9 ) \\circ s e q ( x ) \\circ p a r e n ( y )$

   $f o r a l l ( x , y )$ is the generalization of $y$ by the variable $x$ (provided that $x$ is a variable).

13. succ $n ( 0 , x ) = x$ succ $n ( n + 1 , x ) = s e q ( 3 ) \\circ s u c c \_ { - } n ( n , x )$


succ $. n ( n , x )$ corresponds to the operation of “prepending the sign ‘succ’ in front of $x$ for $n$ times”.

17. numbe $\\begin{array} { r } { \\gimel r ( n ) = s u c c ( n , s e q ( 1 ) ) } \\end{array}$ number $\\cdot ( n )$ is the number-sign for the number $n$ .

18. $s t y p e \_ { 1 } ( x ) \\Leftrightarrow \\exists m , n \\leq x$ . $( m = 1 \\lor v t y p e ( 1 , m ) ) \\land x = s u c c \_ { - } n ( n , s e q ( m ) )$

    $x$ is a sign of type one. 19. ${ \\begin{array} { r l } { s t y p e ( n , x ) \\Leftrightarrow } & { { \\Big ( } n = 1 \\land s t y p e \_ { 1 } ( x ) { \\Big ) } \\lor } \ & { { \\Big ( } n > 1 \\land \\exists v \\leq x { \\cdot } { \\big ( } v t y p e ( n , v ) \\land x = R ( v ) { \\big ) } { \\Big ) } } \\end{array} }$

    $x$ is a sign of type $\\cdot$ .

19. $e l F m ( x ) \\Leftrightarrow \\exists y , z , n \\leq x$ . $( s t y p e ( n , y ) \\land s t y p e ( n + 1 , z ) \\land x = z \\circ p a r e n ( y ) )$

    $x$ is an elementary formula.


$$
o p ( x , y , z ) \\Leftrightarrow ( x = n o t ( y ) ) \\vee ( x = o r ( y , z ) ) \\vee ( \\exists v \\leq x . i s V a r ( v ) \\wedge x = f o r a l l ( v , y ) ) \\vee ( x \\leq y \\leq x ) .
$$

22. $\\begin{array} { r l } { f m S e q ( x ) \\Leftrightarrow \\left( \\forall 0 < n \\leq l e n g t h ( x ) \\cdot \ e l F m ( i t e m ( n , x ) ) \\vee \\right. } & { } \ { \\left. \\exists 0 < p , q < n \\cdot o p ( i t e m ( n , x ) , i t e m ( p , x ) , i t e m ( p , x ) ) \\middle . \\right. } & { } \\end{array}$ m(q, x))

$\\wedge l e n g t h ( x ) > 0$ $x$ is a sequence of formulae, each of which is either an elementary formula or is obtained from the preceding ones by the operations of negation, disjunction, or generalization.

$\\begin{array} { c } { { i s F m ( x ) \\Leftrightarrow \\exists n \\leq \\left( n t h P r i m e ( l e n g t h ( x ) ^ { 2 } ) \\right) ^ { x \\cdot ( l e n g t h ( x ) ) ^ { 2 } } . } } \ { { f m S e q ( n ) \\wedge x = i t e m ( l e n g t h ( n ) , n ) } } \\end{array}$ $x$ is a formula (i.e. the last item of a sequence $n$ of formulae).

$$
\\begin{array} { r l } & { b o u n d ( v , n , x ) \\Leftrightarrow i s V a r ( v ) \\wedge i s F m ( x ) \\wedge } \ & { \\quad \\exists a , b , c \\leq x \\cdot \ x = a \\circ f o r a l l ( v , b ) \\circ c \\wedge i s F m ( b ) \\wedge } \ & { \\qquad l e n g t h ( a ) + 1 \\leq n \\leq l e n g t h ( a ) + l e n g t h ( f o r a l l ( v , b ) ) } \\end{array}
$$

The variable $v$ is bound in $x$ at position $n$ .

25. $f r e e ( v , n , x ) \\Leftrightarrow i s V a r ( v ) \\land i s F m ( x ) \\land$ $v = i t e m ( n , x ) \\wedge n \\leq l e n g t h ( x ) \\wedge \\neg b o u n d ( v , n , x )$

The variable $v$ is free in $x$ at position $n$

26. $f r e e ( v , x ) \\Leftrightarrow \\exists n \\leq l e n g t h ( x ) . f r e e ( v , n , x )$

    $\\boldsymbol { v }$ occurs in $x$ as a free variable.

27. $i n s e r t ( x , n , y ) = \\mathrm { a r g m i n } z \\leq ( n t h P r i m e ( l e n g t h ( x ) + l e n g t h ( y ) ) ) ^ { x + y } .$ $\\exists u , v \\leq x$ . $x = u \\circ s e q ( i t e m ( n , x ) ) \\circ v \\wedge z = u \\circ y \\circ v \\wedge n = l e n g t h ( u ) + 1$


You obtain $i n s e r t ( x , n , y )$ from $x$ by inserting $y$ instead of the $n$ th item in the sequence $x$ (provided that $0 < n \\leq l e n g t h ( x ) \\rangle$ .

28. fre $e P l a c e ( 0 , v , x ) = \\qquad n \\leq l e n g t h ( x )$ . fr $\\begin{array} { r } { \\begin{array} { r } { f r e e ( v , n , x ) \\wedge \\neg \\exists n < p \\leq l e n g t h ( x ) . f r e e ( v , p , x ) } \ { \\neg e P l a c e ( k + 1 \\textit { n } \\textit { r } ) = \\qquad n < t r e e P l a c e ( n \\textit { k } } \\end{array} } \\end{array}$ $e e P l a c e ( k + 1 , v , x ) = \\mathrm { a r g m i n } n < f r e e P l a c e ( n , k , v ) .$ $f r e e ( v , n , x ) \\land \\lnot \\exists n < p < f r e e P l a c e ( n , k , v ) . f r e e ( v , p , x )$

    $f r e e P l a c e ( k , v , x )$ is the $k + 1 \\mathrm { s t }$ place in $x$ (counted from the end of formula $x$ ) where $v$ is free (and 0 if there is no such place).

$\\begin{array} { r l r } { 2 9 . \ n F r e e P l a c e s ( v , x ) = } & { { } \ } & { \ n \\leq l e n g t h ( x ) . \ f r e e P l a c e ( n , v , x ) = 0 } \\end{array}$ nFreePlaces $( v , x )$ is the number of places where $v$ is free in $x$ .

$$
\\begin{array} { r l } & { s u b s t ^ { \\prime } ( 0 , x , v , y ) = x } \ & { s u b s t ^ { \\prime } ( k + 1 , x , v , y ) = i n s e r t ( s u b s t ^ { \\prime } ( k , x , v , y ) , f r e e P l a c e ( k , v , x ) , y ) } \\end{array}
$$

31. $s u b s t ( x , v , y ) = s u b s t ^ { \\prime } ( n F r e e P l a c e s ( v , x ) , x , v , y )$

    $s u b s t ( x , v , y )$ is the above defined concept subs $\\therefore a { \\binom { v } { b } }$ .

32. $i m p ( x , y ) = o r ( n o t ( x ) , y )$ $a n d ( x , y ) = n o t ( o r ( n o t ( x ) , n o t ( y ) ) )$ $e q u i v ( x , y ) = a n d ( i m p ( x , y ) , i m p ( y , x ) )$ $e x i s t s ( v , y ) = n o t ( f o r a l l ( v , n o t ( y ) ) )$

33. typeLif $\\left( n , x \\right) = \\operatorname { a r g m i n } y \\leq x ^ { x ^ { n } }$ . $\\forall k \\leq l e n g t h ( x )$ . $i t e m ( k , x ) \\leq 1 3 \\land i t e m ( k , y ) = i t e m ( k , x ) \\lor$ $i t e m ( k , x ) > 1 3 \\land i t e m ( k , y ) = i t e m ( k , x ) \\cdot p r F a c t o r ( 1 , i t e m ( k , x ) ) ^ { n }$ typeLift $( n , x )$ is the $n$ th type-lift of $x$ (if $x$ and $t y p e L i f t ( n , x )$ are formulae).


There are three specific numbers corresponding to the axioms I, $1$ to 3 (the Peano axioms), which we will denote by $p a \_ { 1 } , p a \_ { 2 } , p a \_ { 3 }$ , and we define:

$3 4 . \ p e a n o A x i o m ( x ) \\Leftrightarrow ( x = p a \_ { 1 } \\lor x = p a \_ { 2 } \\lor x = p a \_ { 3 } )$

$3 5 . \ p r o p I A x i o m ( x ) \\Leftrightarrow \\exists y \\leq x . { i s F m ( y ) } \\land x = { i m p ( o r ( y , y ) , y ) }$ $x$ is a formula that has been obtained by inserting into the axiom schema II, 1. We define prop2Axiom(x), prop3Axiom(x), and $p r o p 4 A x i o m ( x )$ analogously.

$3 6 . \ p r o p A x i o m ( x ) \\Leftrightarrow p r o p I A x i o m ( x ) \\lor p r o p 2 A x i o m ( x ) \\lor p r o p 3 A x i o m ( x ) \\lor p r o p 4 X i s$ Axiom(x) $x$ is a formula that has been obtained by inserting into on of the proposition axioms.

37. quantor1Axiom $\\begin{array} { r } { \\gamma o n d i t i o n ( z , y , v ) \\Leftrightarrow \\neg \\exists n \\leq l e n g t h ( y ) , m \\leq l e n g t h ( z ) , w \\leq z . } \\end{array}$ $w = i t e m ( m , z ) \\wedge b o u n d ( w , n , y ) \\wedge f r e e ( v , n , y )$

$z$ does not contain a variable that is bound anywhere in $y$ where $\\boldsymbol { v }$ is free. This condition for the applicability of axiom III, $^ { 1 }$ , ensured that a substitution of $z$ for the free occurrences of $\\boldsymbol { v }$ in $y$ does not accidentally bind some of $z$ ’s variables.

38. $q u a n t o r 1 A x i o m ( x ) \\Leftrightarrow \\exists v , y , z , n \\leq x$ .$v t y p e ( n , v ) \\wedge s t y p e ( n , z ) \\wedge i s F m ( y ) \\wedge q u a n t o r I A x i o m C o n d i t i o n ( z , y , v ) \\wedge$ $x = i m p ( f o r a l l ( v , y ) , s u b s t ( y , v , z ) )$

$x$ is a formula obtained by substitution from the axiom schema III, $1$ , i.e. one of the quantor axioms.

39. $q u a n t o r 2 A x i o m ( x ) \\Leftrightarrow \\exists v , q , p \\leq x$ . $i s V a r ( v ) \\wedge i s F m ( p ) \\wedge \\neg f r e e ( v , p ) \\wedge i s F m ( q ) \\wedge$ $x = i m p ( f o r a l l ( v , o r ( p , q ) )$ , $o r ( p , f o r a l l ( v , q ) ) ,$ )

$x$ is a formula obtained by substitution from the axiom schema III, 2, i.e. the other one of the quantor axioms.

4 $. 0 . \ r e d u A x i o m ( x ) \\Leftrightarrow \\exists u , v , y , n \\leq x$ . $\\mathit { v t y p e ( n , v ) } \\wedge \\mathit { v t y p e ( n + 1 , u ) } \\wedge \\neg \\mathit { f r e e ( u , y ) } \\wedge \\mathit { i s F m ( y ) } \\wedge$ $x = e x i s t s ( u , f o r a l l ( v , e q u i v ( s e q ( u ) \\circ p a r e n ( s e q ( v ) ) , y ) ) )$

$x$ is a formula obtained by substitution from the axiom schema IV, 1, i.e. from the reducibility axiom.

There is a specific number corresponding to axiom V, $\_ 1$ , (the set axiom), which we will denote by $s a$ , and we define:

$4 1 . \ s e t A x i o m ( x ) \\Leftrightarrow \\exists n \\leq x . x = t y p e L i f t ( n , s a )$

42. $i s A x i o m ( x ) \\Leftrightarrow p e a n o A x i o m ( x ) \\lor p r o p A x i o m ( x ) \\lor$ $q u a n t o r I A x i o m ( x ) \\vee q u a n t o r \\mathcal { Q } A x i o m ( x ) \\vee r e d u A x i o m ( x ) \\vee$ ∨ $s e t A x i o m ( x )$

$x$ is an axiom.

$4 3 . \ i m m C o n s e q ( x , y , z ) \\Leftrightarrow y = i m p ( z , x ) \\lor \\exists v \\leq x . \ i s V a r ( v ) \\land x = f o r a l l ( v , y )$ $x$ is an immediate consequence of $y$ and $z$ .

$\\begin{array} { r l } & { \\mathfrak { s } P r o o f F i g u r e ( x ) \\Leftrightarrow ( \\forall 0 < n \\le l e n g t h ( x ) . } \ & { i s A x i o m ( i t e m ( n , x ) ) \\vee \\exists 0 < p , q < n . } \ & { i m m C o n s e q ( i t e m ( n , x ) , i t e m ( p , x ) , i t e m ( q , x ) ) ) \\wedge } \\end{array}$ $l e n g t h ( x ) > 0$

is a proof figure (a finite sequence of formulae, each of which is either an axiom or the immediate consequence of two of the preceding ones).

$4 5 . \ p r o o f F o r ( x , y ) \\Leftrightarrow i s P r o o f F i g u r e ( x ) \\wedge i t e m ( l e n g t h ( x ) , x ) = y$ $x$ is a proof for the formula $y$ .

4 $6 . \ p r o v a b l e ( x ) \\Leftrightarrow \\exists y . \ p r o o f F o r ( y , x )$

$x$ is a provable formula. $( p r o v a b l e ( x )$ is the only one among the concepts 1-46 for which we can not assert that it is primitive recursive).

# 2.5 Denotability and provability

The fact that can be expressed vaguely by: Every primitive recursive relation is definable within system $P$ (interpreting that system as to content), will be expressed in the following theorem without referring to the interpretation of formulae of $\\cdot$ :

Theorem V: For every primitive recursive relation $R ( x \_ { 1 } , \\ldots , x \_ { n } )$ there is a relation sign $r$ (with the free variables $u \_ { 1 } , \\ldots , u \_ { n } /$ , such that for each $n$ -tuple $( x \_ { 1 } , \\ldots , x \_ { n } )$ the following holds:

We contend ourselves with giving a sketchy outline of the proof for this theorem here, since it does not offer any difficulties in principle and is rather cumbersome. We prove the theorem for all relations $R ( x \_ { 1 } , \\ldots , x \_ { n } )$ of the form $x \_ { 1 } = \\phi ( x \_ { 2 } , \\ldots , x \_ { n } )$ (where $\\phi$ is a primitive recursive function) and apply natural induction by $\\phi$ ’s degree. For functions of degree one (i.e. constants and the function $x + 1$ ) the theorem is trivial. Hence, let $\\phi$ be of degree $m$ . It is built from functions of lower degree $\\phi \_ { 1 } , \\ldots , \\phi \_ { k }$ by the operations of insertion and primitive recursive definition. Since everything has already been proven for $\\phi \_ { 1 } , \\ldots , \\phi \_ { k }$ by the inductive assumption, there are corresponding relation signs $r \_ { 1 } , \\ldots , r \_ { k }$ such that (3), (4) hold. The definition processes by which $\\phi$ is built from $\\phi \_ { 1 } , \\ldots , \\phi \_ { k }$ (insertion and primitive recursion) can all be modeled formally in system $\\cdot$ . Doing this, one gets from $r \_ { 1 } , \\ldots , r \_ { k }$ a new relation sign $r$ for which one can proof the validity of (3), (4) without difficulties. A relation sign $r$ associated with a primitive recursive relation in this manner shall be called primitive recursive.

# 2.6 Undecidability theorem

We now come to the goal of our elaborations. Let $\\kappa$ be any class of formulae. We denote with $C o n s e q ( \\kappa )$ the smallest set of formulae that contains all formulae of $\\kappa$ and all axioms and is closed under the relation “immediate consequence”. $\\kappa$ is called $\\omega$ -consistent if there is no class-sign $a$ such that

$$
\\left( \\forall n \\cdot s u b s t ( a , v , n u m b e r ( n ) ) \\in C o n s e q ( \\kappa ) \\right) \\wedge n o t ( f o r a l l ( v , a ) ) \\in C o n s e q ( \\kappa )
$$

where $\\boldsymbol { v }$ is the free variable of the class-sign $a$ . With other words, a witness against $\\omega$ -consistency would be a formula $a$ with one free variable where we can derive $a ( n )$ for all $n$ , but also $\\neg \\forall n \\cdot a ( n )$ , a contradiction.

Every $\\omega$ -consistent system is, of course, also consistent. The reverse, however, does not hold true, as will be shown later. We call a system consistent if there is no formula $a$ such that both $a$ and $\\lnot$ are provable. Such a formula would be a witness against the consistency, but in general not against the $\\boldsymbol { \\cdot }$ -consistency. With other words, $\\boldsymbol { \\mathscr { N } }$ -consistency is stronger than consistency: the first implies the latter, but not vice versa.

The general result about the existence of undecidable propositions goes as follows:

Theorem VI: For every $\\omega$ -consistent primitive recursive class $\\kappa$ of formulae there is a primitive recursive class-sign $r$ such that neither forall $\\boldsymbol { \\mathbf { \\mathit { \\chi } } } ( v , r )$ nor $n o t ( f o r a l l ( v , r ) )$ belongs to Conseq(κ) (where $\\boldsymbol { v }$ is the free variable of $r$ ).

Since the premise in the theorem is $\\cdot$ -consistency, which is stronger than consistency, the theorem is less general than if its premise were just consistency.

Proof: Let $\\kappa$ be any $\\omega$ -consistent primitive recursive class of formulae. We define:

$$
\\begin{array} { r l } & { i s P r o o f F i g u r e \_ { \\kappa } ( x ) \\Leftrightarrow } \ & { \\quad \\Bigl ( \\forall n \\leq l e n g t h ( x ) . i s A x i o m ( i t e m ( n , x ) ) \\vee \\left( i t e m ( n , x ) \\in \\kappa \\right) \\vee } \ & { \\quad \\exists 0 < p , q < n . i m m e d C o n s e q ( i t e m ( n , x ) , i t e m ( p , x ) , i t e m ( q , x ) ) \\Bigr ) \\wedge } \ & { l e n g t h ( x ) > 0 } \\end{array}
$$

(compare to the analogous concept 44)

$$
\\begin{array} { c } { { p r o o f F o r \_ { \\kappa } ( x , y ) \\Leftrightarrow i s P r o o f F i g u r e \_ { \\kappa } ( x ) \\wedge i t e m ( l e n g t h ( x ) , x ) = y } } \ { { p r o v a b l e \_ { \\kappa } ( x ) \\Leftrightarrow \\exists y . p r o o f F o r \_ { \\kappa } ( y , x ) } } \\end{array}
$$

(compare to the analogous concepts 45, 46).

The following obviously holds:

$$
\\begin{array} { c } { { \\eta } \_ { \\mathcal { X } } . \\left( p r o v a b l e \_ { \\kappa } ( x ) \\Leftrightarrow x \\in C o n s e q ( \\kappa ) \\right) } \ { { \\forall x . \\left( p r o v a b l e ( x ) \\Rightarrow p r o v a b l e \_ { \\kappa } ( x ) \\right) . } } \\end{array}
$$

Now we define the relation:

$$
Q ( x , y ) \\Leftrightarrow \\neg { \\big ( } p r o o f F o r \_ { \\kappa } ( x , s u b s t ( y , 1 9 , n u m b e r ( y ) ) ) { \\big ) } .
$$

Intuitively $Q ( x , y )$ means $x$ does not prove $y ( y )$ .

Since proofFor ${ \\bf \\Phi } \_ { \\kappa } ( x , y )$ (by (6), (5)) and $s u b s t ( y , 1 9 , n u m b e r ( y ) )$ ) (by definitions 17, 31) are primitive recursive, so is $Q ( x , y )$ . According to theorem V we hence have a relation sign $q$ (with the free variables 17, 19) such that the following holds:

$$
\\begin{array} { r l } & { \\quad \\neg p r o o f F o r \_ { \\kappa } ( x , s u b s t ( y , 1 9 , n u m b e r ( y ) ) ) \\Rightarrow } \ & { p r o v a b l e \_ { \\kappa } ( s u b s t ( q , 1 7 1 9 , n u m b e r ( x ) \ n u m b e r ( y ) ) ) } \ & { \\qquad p r o o f F o r \_ { \\kappa } ( x , s u b s t ( y , 1 9 , n u m b e r ( y ) ) ) \\Rightarrow } \ & { p r o v a b l e \_ { \\kappa } ( n o t ( s u b s t ( q , 1 7 1 9 , n u m b e r ( x ) \ n u m b e r ( y ) ) ) ) . } \\end{array}
$$

We set:

$$
p = f o r a l l ( 1 7 , q )
$$

( $p$ is a class-sign with the free variable 19 (which intuitively means 19(19), i.e. $y ( y )$ , is improvable)) and

$$
r = s u b s t ( q , 1 9 , n u m b e r ( p ) )
$$

( $r$ is a primitive recursive class-sign with the free variable 17 (which intuitively means that 17, i.e. $\\cdot$ , does not prove $p ( p )$ , where $p ( p )$ means $p ( p )$ is unprovable)).

Then the following holds:

$$
\\begin{array} { c } { { s u b s t ( p , 1 9 , n u m b e r ( p ) ) = s u b s t ( f o r a l l ( 1 7 , q ) , 1 9 , n u m b e r ( p ) ) } } \ { { = f o r a l l ( 1 7 , s u b s t ( q , 1 9 , n u m b e r ( p ) ) ) } } \ { { = f o r a l l ( 1 7 , r ) } } \\end{array}
$$

(because of (11 and 12)); furthermore:

$$
s u b s t ( q , 1 7 ~ 1 9 , n u m b e r ( x ) ~ n u m b e r ( p ) ) = s u b s t ( r , 1 7 , n u m b e r ( x ) )
$$

(because of (14)). The recurring $f o r a l l ( 1 7 , r )$ can be interpreted as there is no prove for $p ( p )$ , with other words, $f o r a l l ( 1 7 , r )$ states that the statement $p ( p )$ that states its own improvability is improvable. If we now insert $p$ for $y$ in (9) and (10), we get, taking (13) and (14) into account:

$$
\\begin{array} { r l } & { \\quad \\neg p r o o f F o r \_ { \\kappa } ( x , f o r a l l ( 1 7 , r ) ) \\Rightarrow p r o v a b l e \_ { \\kappa } ( s u b s t ( r , 1 7 , n u m b e r ( x ) ) ) } \ & { \\quad p r o o f F o r \_ { \\kappa } ( x , f o r a l l ( 1 7 , r ) ) \\Rightarrow p r o v a b l e \_ { \\kappa } ( n o t ( s u b s t ( r , 1 7 , n u m b e r ( x ) ) ) ) } \\end{array}
$$

This yields:

1. forall(17, r) is not $\\kappa$ -provable. Because if that were the case, there would (by (7)) exist an $n$ such that $p r o o f F o r \_ { \\kappa } ( n , f o r a l l ( 1 7 , r ) )$ . By (16) we would hence have:

$$
p r o v a b l e \_ { \\kappa } \\big ( n o t ( s u b s t ( r , 1 7 , n u m b e r ( n ) ) ) \\big ) ,
$$

while on the other hand the $\\kappa$ -provability of $f o r a l l ( 1 7 , r )$ also implies that of $s u b s t ( r , 1 7 , n u m b e r ( n ) )$ . Therefore $\\kappa$ would be inconsistent (and in particular $\\omega$ - inconsistent).

2. $n o t ( f o r a l l ( 1 7 , r ) )$ is not $\\kappa$ -provable. Proof: As has just been shown, $f o r a l l ( 1 7 , r )$ is not $\\kappa$ -provable, i.e. (by (7)) we have

$$
\\forall n \\neg p r o o f F o r \_ { \\kappa } ( n , f o r a l l ( 1 7 , r ) ) .
$$

This implies by (15)

$$
\\forall n . p r o v a b l e \_ { \\kappa } ( s u b s t ( r , 1 7 , n u m b e r ( n ) ) )
$$

which would, together with

$$
p r o v a b l e \_ { \\kappa } ( n o t ( f o r a l l ( 1 7 , r ) ) ) ,
$$

contradict the $\\cdot$ -consistency of $\\kappa$ .

Therefore $f o r a l l ( 1 7 , r )$ is not decidable from $\\kappa$ , whereby theorem VI is proved.

# 2.7 Discussion

One can easily convince oneself that the proof we just did is constructive, i.e. it the following is intuitionistically flawlessly proven:

Let any primitive recursively defined class $\\kappa$ of formulae be given. Then if the formal decision (from $\\kappa$ ) of the proposition-formula forall $\\left. \\left( 1 7 , r \\right) \\right.$ is also given, one can effectively present:

1. A proof for $n o t ( f o r a l l ( 1 7 , r ) )$ ).

2. For any given $n$ a proof for $s u b s t ( r , 1 7 , n u m b e r ( n ) )$ ), i.e. a formal decision for forall $\\left\[ ( 1 7 , r \\right)$ would imply the effective presentability of an $\\omega$ -inconsistency-proof.\
\
\
Let us call a relation (class) between natural numbers $R ( x \_ { 1 } , \\ldots , x \_ { n } )$ decision-definite if there is an $n$ -ary relation sign $r$ such that (3) and (4) (c.f. theorem V) hold. In particular therefore every primitive recursive relation is by Theorem V decision-definite. Analogously, a relation sign shall be called decision-definite if it corresponds to a decision-definite relation in this manner. For the existence of propositions undecidable from $\\kappa$ it is now sufficient to require of a class $\\kappa$ that it is $\\omega$ -consistent and decisiondefinite. With other words, it is not even important how the class of added axioms $\\kappa$ is defined, we just have to be able to decide with the means of the system whether something is an axiom or not. This is because the decision-definiteness carries over from $\\kappa$ to $p o o f F o r \_ { \\kappa } ( x , y )$ (compare to (5), (6)) and to $Q ( x , y )$ (compare to (9)), and only that was used for the above proof. In this case, the undecidable theorem takes on the form $f o r a l l ( v , r )$ , where $r$ is a decision-definite class-sign (by the way, it is even sufficient that $\\kappa$ is decision-definite in the system augmented by $\\kappa$ ).\
\
If instead of $\\omega$ -consistency we only assume consistency for $\\kappa$ , then, although the existence of an undecidable proposition does not follow, there follows the existence of a property $( r )$ for which a counter-example is not presentable and neither is it provable that the relation holds for all numbers. Because for the proof that $f o r a l l ( 1 7 , r )$ is not $\\omega$ -provable we only used the $\\omega$ -consistency of $\\kappa$ (compare to page 189), and $\\neg p r o v a b l e \_ { \\kappa } ( f o r a l l ( 1 7 , r ) )$ implies by (15) for each number $x$ that $s u b s t ( r , 1 7 , n u m b e r ( x ) )$ ) holds, i.e. that for no number $n o t ( s u b s t ( r , 1 7 , n u m b e r ( x ) )$ ) is provable.\
\
If you add $n o t ( f o r a l l ( 1 7 , r ) )$ to $\\kappa$ you get a consistent but not $\\omega$ -consistent class of formulae $\\kappa ^ { \\prime }$ . $\\kappa ^ { \\prime }$ is consistent because otherwise $f o r a l l ( 1 7 , r )$ would be provable. But $\\kappa ^ { \\prime }$ is not $\\omega$ -consistent, since because of $\\neg p r o v a b l e \_ { \\kappa } ( f o r a l l ( 1 7 , r ) )$ and (15) we have\
\
$$\
\\forall x . p r o v a b l e \_ { \\kappa } ( s u b s t ( r , 1 7 , n u m b e r ( x ) ) ) ,\
$$\
\
and hence in particular\
\
$$\
\\forall x . p r o v a b l e \_ { \\kappa ^ { \\prime } } ( s u b s t ( r , 1 7 , n u m b e r ( x ) ) ) ,\
$$\
\
and on the other hand of course\
\
$$\
\\begin{array} { r } { p r o v a b l e \_ { \\kappa ^ { \\prime } } ( \\lnot f o r a l l ( 1 7 , r ) ) . } \\end{array}\
$$\
\
But that means that $f o r a l l ( 1 7 , r )$ precisely fits the definition of a witness against $\\omega$ - consistency.\
\
A special case of theorem VI is the theorem where the class $\\kappa$ consists of a finite number of formulae (and perhaps the ones derived from these by type-lift). Every finite class $\\kappa$ is of course primitive recursive. Let $a$ be the largest contained number. Then we have for $\\kappa$ in this case\
\
$$\
x \\in \\kappa \\Leftrightarrow \\exists m \\leq x , n \\leq a . n \\in \\kappa \\land x = t y p e L i f t ( m , n )\
$$\
\
Hence, $\\kappa$ is primitive recursive. This allows us to conclude for example that also with the help of the axiom of choice (for all types) or the generalized continuum hypothesis not all propositions are decidable, assuming that these hypotheses are $\\omega$ -consistent.\
\
During the proof of theorem VI we did not use any other properties of the system $P$ than the following:\
\
1. The class of axioms and deduction rules (i.e. the relation “immediate consequence”) are primitive recursively definable (as soon as you replace the basic signs by numbers in some way).\
2. Every primitive recursive relation is definable within the system $\\cdot$ (in the sense of theorem V).\
\
Hence there are undecidable propositions of the form $\\forall x . F ( x )$ in every formal system that fulfills the preconditions 1, 2 and is $\\omega \\cdot$ -consistent, and also in every extension of such a system by a primitive recursively definable, $\\omega$ -consistent class of axioms. To this kind of systems belong, as one can easily confirm, the Zermelo-Fraenkelian axiomsystem and the von Neumannian system of set-theory, furthermore the axiom-system of number-theory which consists of the Peano axioms, primitive recursive definition (by schema (2)) and the logical deduction rules. Simply every system whose deduction rules are the usual ones and whose axioms (analogously like in $\\cdot$ ) are made by insertion into a finite number of schemas fulfills precondition 1.\
\
# 3 Generalizations\
\
omitted—\
\
# 4 Implications for the nature of consistency\
\
omitted—\
\
# A Experiences\
\
This translation was done for a reason. I took Mike Eisenberg’s class “Computer Science: The Canon” at the University of Colorado in fall 2000. It was announced as a “great works” lecture-and-discussion course, offering an opportunity to be pointed to some great papers, giving an incentive to read them, and providing a forum for discussion. This also explains my motivation for translating G¨odel’s proof: it is a truly impressive and fascinating paper, there is some incentive in completing my final paper for a class, and this exercise should and did benefit me intellectually. Here, I will try to share the experiences I made doing the translation. I deliberately chose a personal, informal style for this final section to stress that what I write here are just my opinions, nothing less and nothing more.\
\
# A.1 Have I learned or gained something?\
\
First of all, how useful is it to read this paper anyway, whether you translate it or not? One first answer that comes to mind is that the effort of understanding it hones abstract thinking skills, and that some basic concepts like Peano axioms, primitive recursion, or consistency are nicely illustrated and shown in a motivated context. The difficulty with this argument is that it is self-referential: we read this paper to hone skills that we would not need to hone if we would not read this kind of papers. I don’t really have a problem with that, people do many things for their own sake, but fortunately there are other gains to be had from reading this paper. One thing that I found striking is how I only fully appreciated the thoughts from section 2.7 on re-reading the proof. I find it fascinating just how general the result is: your formal system does not need to be finite, or even primitive recursively describable, no, it suffices that you can decide its set of axioms in itself. I am not sure whether other people are as fascinated by this as I am; if you are not, try to see what I mean, it’s worth the effort! But in any case, I have gained an appreciation for the beauty and power of the results, which I am happy for. Finally, there is some hope that the writing skills, proof techniques, and thought processes exhibited by this paper might rub off, so to speak. Part of learning an art is to study the masters, and G¨odel was clearly a master in his art!\
\
Second, how useful was the translation itself? Well, it was useful to try out some ideas I had about how translating a technical paper between languages might work. My recipe was to first read and understand the whole paper, then translate it one sentence at a time (avoid to start translating a sentence before having a plan for all of it!), and finally to read it fast to check the flow and logic. This might or might not be the best way, but it worked well enough for me. For understanding the paper itself, the translation between languages or the use of hyper-text as a medium did not help me much as I was doing it. More important was the translation of notation to one I am more used to, and the occasional comment to express my view of a tricky detail. Last but not least, it seems hardly necessary to admit my strong affection for type-setting, and there is a certain pleasure in looking over and polishing something you crafted that\
\
I believe I share with many people.\
\
# A.2 Has the paper improved?\
\
The original paper is brilliant, well-written, rich of content, relevant. Yet I went ahead and tinkered around, changing a little thing here and there, taking much more freedom than the translators for \[2, 1\]. Yes, the paper did improve! It is closer to my very personal ideas of what it should ideally look like. To me who did the changes just a few days ago the modified paper looks better than the original.\
\
In section 0, I announced a translation along three dimensions, namely language (from German to English), notation (using symbols I am more used to) and medium (exploiting hyper-text). Let us review each one in turn and criticize the changes.\
\
Language. After finishing the translation, I compared it with the ones in \[2, 1\], and found that although they are different, the wording probably does not matter all that much. To give an example where it did seem to play a role, here are three wordings for besteht eine nahe Verwandtschaft: (i) is closely related, (ii) is also a close relationship, (iii) is also a close kinship. The third one is mine, and my motivation for it is that it is the most punchy one, for what it’s worth. The stumbling blocks in this kind of translation, as I see it, are rather the technical terms that may be in no dictionary. For example, I could well imagine that my translation decision-definite seems unnatural to someone studying logic who might be used to another term.\
\
Notation. This is the part of the translation that I believe helps the most in making the paper more accessible for readers with a similar educational background as mine. For example, I have never seen “Π” used for $" \\forall "$ , and inside an English text I find $\\cdot b o u n d ( v , n , x ) ^ { \\prime \\prime }$ easier to parse than ${ } ^ { \\mathfrak { a } } v \\operatorname { G e b } n , x ^ { \\mathfrak { n } }$ .\
\
Hyper-text. During the translation, it became clearer to me just how very “hypertext” the paper already was! On the one hand, the fact that one naturally refers back to definitions and theorems underlines that hyper-text is a natural way of presentation. On the other hand, the fact that one gets along quite well with a linear text, relying on the readers to construct the thought-building in their own head, seems to suggest that the change of medium was in fact rather superficial. I would be interested in the opinions of readers of this document on this: did the hyper-text improve the paper?\
\
Clearly, the most important aspects of the paper are still the organization, writing, and explanation skills of G¨odel himself. And clearly, the paper is still an intellectual challenge, yielding its rewards only to the fearless. To assume that my work has changed either of these facts significantly would be presumptuous.\
\
# A.3 Opinions\
\
This discussion is a trade-off between being careful and thoughtful on the one hand, and being forthcoming and fruitful on the other. As it leans more to the second half of the spectrum, I might as well go ahead and state some opinions the project and the reflections upon it have inspired in me.\
\
• A well-written technical paper already has the positive features of hyper-text. This may not seem so at first glance, but compare it to the typical web-page and then ask yourself which has more coherence. To me, coherence is part of the essence and beauty of cross-referencing.\
\
• There is an analogy between writing papers and computer programs, and it is amazing how far you can stretch it without it breaks down. The skill of gradually building up your vocabulary, dividing and conquering the task in a clean and skillful way, and commenting on what you do are all illustrated nicely by G¨odel’s proof.\
\
• Reading and understanding G¨odel’s proof yields many benefits. There are pearls to be found in its contents, and skills to be practiced that go beyond what one might think at first glance.\
\
I am well aware that I did not give many arguments to support these opinions. That would be the stuff for a paper by itself, and the reader is encouraged to think about them. But above all, enjoy the paper “On formally undecidable propositions of Principia Mathematica and related systems I” itself, which after all makes up the main part of this document!\
\
# Literatur\
\
\[1\] Kurt G¨odel. On Formally Undecidable Propositions of Principia Mathematica and Related Systems. Dover, 1962.\
\
\[2\] Kurt G¨odel. Uber formal unentscheidbare S ¨ ¨atze der Principia Mathematica und verwandter Systeme I. In Solomon Feferman, editor, Kurt G¨odel: Collected Works, volume 1, pages 144–195. Oxford University Press, 1986. German text, parallel English translation.\
\
# B Index\
\
$\\alpha$ , 8\
\
$\\beta$ , 8\
\
$\\gamma$ , 8\
\
$\\omega$ -consistent, 14\
\
$n$ -ary relation sign, 4\
\
argmin, 7\
\
subst, 4\
\
proof figure, 13\
\
axiom, 5 basic sign, 4\
\
class-sign, 3\
\
comprehension axiom, 5\
\
consistent, 14\
\
decision-definite, 17\
\
degree, 7\
\
disjunction, 4\
\
elementary formula, 4\
\
formula, 4\
\
generalization, 4\
\
immediate consequence, 6\
\
negation, 4\
\
number-sign, 4\
\
$P$ , 4\
\
Peano axioms, 5\
\
primitive recursion, 7\
\
primitive recursive, 7\
\
PM, 2\
\
proof, 2\
\
proposition-formula, 4\
\
proposition axioms, 5\
\
provable, 6\
\
quantor axioms, 5\
\
reducibility axiom, 5\
\
set axiom, 6\
\
sign of type $n$ , 4\
\
sign of type one, 4\
\
type-lift, 5\
\
variable of type one, 4\
\
variable of type $n$ , 4\
\
variable of type two, 4