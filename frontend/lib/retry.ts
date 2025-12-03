/**
 * Retry a function with exponential backoff
 * Useful for handling transient errors from browser automation
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    initialDelay?: number;
    maxDelay?: number;
    retryable?: (error: any) => boolean;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    retryable = (error: any) => {
      // Retry on 400 errors (likely browser navigation issues) or network errors
      const status = error.response?.status;
      const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout');
      const isNetworkError = !error.response && error.request;
      const errorDetail = error.response?.data?.detail || '';
      // Check if error is related to browser navigation (transient)
      const isNavigationError = errorDetail.includes('Failed to navigate') || 
                                errorDetail.includes('ERR_ABORTED') ||
                                errorDetail.includes('Page.goto');
      
      return status === 400 || isTimeout || isNetworkError || isNavigationError;
    },
  } = options;

  let lastError: any;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;

      // Don't retry if it's the last attempt or error is not retryable
      if (attempt === maxRetries || !retryable(error)) {
        throw error;
      }

      // Log retry attempt for debugging
      console.log(`Retrying request (attempt ${attempt + 1}/${maxRetries}) after ${delay}ms...`);

      // Wait before retrying with exponential backoff
      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, maxDelay);
    }
  }

  throw lastError;
}

