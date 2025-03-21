import { Transition } from '@headlessui/react';
import React from 'react';

import { BotAvatar } from '@/components/Avatar';
import { Text } from '@/components/Shared';
import { BotState } from '@/types/message';

type Props = {
  show: boolean;
};

/**
 * @description Welcome message shown to the user when they first open the chat.
 */
export const Welcome: React.FC<Props> = ({ show }) => {
  return (
    <Transition
      show={show}
      appear
      className="flex flex-col items-center gap-y-4"
      enter="transition-all duration-300 ease-out delay-300"
      enterFrom="opacity-0"
      enterTo="opacity-100"
      leave="transition-opacity duration-200"
      leaveFrom="opacity-100"
      leaveTo="opacity-0"
      as="div"
    >
      <div className="flex h-7 w-7 items-center justify-center rounded bg-secondary-400 md:h-9 md:w-9">
        <BotAvatar state={BotState.FULFILLED} style="secondary" />
      </div>
      <Text styleAs="p-lg" className="text-center text-secondary-800 md:!text-h4">
        Need help? Your wish is my command.
      </Text>
    </Transition>
  );
};
