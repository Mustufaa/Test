def longestValidParentheses(s):
    
    stack = [-1]
    max_length = 0

    for i in range(len(s)):
        if s[i] == '(':
            # push index of opening bracket
            stack.append(i)
        else:
            # it's a closing bracket, pop the top
            stack.pop()

            if len(stack) == 0:
                # nothing left to match with, so this becomes new base
                stack.append(i)
            else:
                # valid substring found, calculate its length
                length = i - stack[-1]
                if length > max_length:
                    max_length = length

    return max_length


#  Test Cases
s1 = "(()"
print(longestValidParentheses(s1))   # Output: 2

s2 = ")()())"
print(longestValidParentheses(s2))   # Output: 4

s3 = ""
print(longestValidParentheses(s3))   # Output: 0