import { inject } from 'vue';
import { createLogger } from '@/core/logger';

/**
 * Get a namespaced logger inside any component.
 * @param {string} namespace
 */
export function useLogger(namespace) {
  // Try to reuse the injected root logger's config, else fall back
  const injected = inject('$log', null);
  return injected ? injected.child(namespace) : createLogger(namespace);
}
/*usage
useLogger → only inside Vue components (or other composables).
createLogger → everywhere else (plain JS: usecases, repos, datasources, router, DI container, etc.).

import { createLogger } from '@/core/logger';

const log = createLogger('GetAgreementsUseCase');
usage log.debug(`→ ${config.method?.toUpperCase()} ${config.url}`, config.data);


import { useLogger } from '@/presentation/composables/useLogger';

const log = useLogger('AgreementsView');
  log.info('Agreements view mounted');

*/