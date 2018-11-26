Direct Commands:\n
~~~~~~~~~~~~~~~~\n
% for group_name, command_list in direct_commands.items():
    <%
        title_line = '^' * len(group_name)
    %>
    \n
    ${group_name}\n
    ${title_line}\n
    \n
    % for command in command_list:
        <%
            args = [f'<{arg}>' for arg in command['args']]
            args_string = ' '.join(args)
            command_string = command['command']
            if args_string:
                command_string += f' {args_string}'
            text = f'-\ \ ``/{command_string}`` - {command["description"]}'

        %>
        ${text}\n
    % endfor
% endfor
\n
\n
Indirect Commands:\n
~~~~~~~~~~~~~~~~~~\n
\n
% for group_name, command_list in indirect_commands.items():
    <%
        title_line = '^' * len(group_name)
    %>
    ${group_name}\n
    ${title_line}\n
    \n
    % for command in command_list:
        -\ \ **${command['title']}** - ${command['description']}\n
    % endfor
% endfor


BE SURE TO REPLACE "\ \ " with 2 whitespaces
