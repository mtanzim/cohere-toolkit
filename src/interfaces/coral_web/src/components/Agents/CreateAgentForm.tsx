import { useRouter } from 'next/router';
import React, { useState } from 'react';

import { AgentForm, AgentFormFieldKeys, AgentFormFields } from '@/components/Agents/AgentForm';
import { Button, Text } from '@/components/Shared';
import { useCreateAgent, useIsAgentNameUnique } from '@/hooks/agents';
import { useParamsStore } from '@/stores';

/**
 * @description Form to create a new agent.
 */
export const CreateAgentForm: React.FC = () => {
  const router = useRouter();
  const { mutateAsync: createAgent } = useCreateAgent();
  const {
    params: { preamble },
  } = useParamsStore();
  const isAgentNameUnique = useIsAgentNameUnique();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fields, setFields] = useState<AgentFormFields>({
    name: '',
    description: '',
    preamble,
    deployment: '',
    model: '',
    tools: [],
  });

  const fieldErrors = {
    ...(isAgentNameUnique(fields.name) ? {} : { name: 'Assistant name must be unique' }),
  };

  const canSubmit = (() => {
    const { tools, preamble, ...requredFields } = fields;
    return Object.values(requredFields).every(Boolean) && !Object.keys(fieldErrors).length;
  })();

  const handleChange = (key: Omit<AgentFormFieldKeys, 'tools'>, value: string) => {
    setFields({
      ...fields,
      [key as string]: value,
    });
  };

  const handleToolToggle = (toolName: string, checked: boolean) => {
    const enabledTools = [...(fields.tools ? fields.tools : [])];
    setFields({
      ...fields,
      tools: checked ? [...enabledTools, toolName] : enabledTools.filter((t) => t !== toolName),
    });
  };

  const handleSubmit = async () => {
    if (!canSubmit) return;

    try {
      setIsSubmitting(true);
      await createAgent(fields);
      setFields({
        name: '',
        description: '',
        preamble,
        deployment: '',
        model: '',
        tools: [],
      })
      router.push('/agents', undefined, { shallow: true });
    } catch (e) {
      console.error(e);
    }
    setIsSubmitting(false);
  };

  return (
    <div className="relative h-full w-full">
      <div className="flex h-full max-w-[650px] flex-col gap-y-2 p-10 overflow-scroll">
        <Text styleAs="h4">Create an Assistant</Text>
        <Text className="text-volcanic-700">
          Create an unique assistant and share with your org
        </Text>
        <AgentForm
          fields={fields}
          onChange={handleChange}
          onToolToggle={handleToolToggle}
          errors={fieldErrors}
          className="mt-6"
        />
      </div>
      <div className="absolute bottom-0 right-0 flex w-full justify-end border-t border-marble-400 bg-white px-4 py-8">
        <Button splitIcon="add" onClick={handleSubmit} disabled={!canSubmit || isSubmitting}>
          {isSubmitting ? 'Creating assistant' : 'Create'}
        </Button>
      </div>
    </div>
  );
};
